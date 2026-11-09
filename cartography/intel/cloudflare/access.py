import ipaddress
import json
import logging
import re
from typing import Any
from urllib.parse import urlsplit

import neo4j
from cloudflare import APIError
from cloudflare import Cloudflare

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.cloudflare.accessapplication import (
    CloudflareAccessApplicationSchema,
)
from cartography.models.cloudflare.accesspolicy import CloudflareAccessPolicySchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: Cloudflare,
    common_job_parameters: dict[str, Any],
    account_id: str,
    zones: list[dict[str, Any]],
    dns_records: list[dict[str, str]],
) -> None:
    # Finish every API read before writing. A failed application/policy page must
    # not look like an empty inventory or partially replace the previous graph.
    try:
        applications = get_applications(client, account_id)
        policies = [
            (application["id"], application.get("policies") or [])
            for application in applications
        ]
    except APIError as exc:
        logger.warning(
            "Unable to read Cloudflare Access applications and policies for account %s. "
            "Skipping Access loading and cleanup; check the token's Access read permissions. "
            "Error: %s (HTTP %s).",
            account_id,
            type(exc).__name__,
            getattr(exc, "status_code", None),
        )
        return

    application_data = transform_applications(
        applications, account_id, zones, dns_records
    )
    policy_data = [
        row
        for application_id, application_policies in policies
        for row in transform_policies(application_policies, account_id, application_id)
    ]
    update_tag = common_job_parameters["UPDATE_TAG"]
    load_applications(neo4j_session, application_data, account_id, update_tag)
    load_policies(neo4j_session, policy_data, account_id, update_tag)
    cleanup(neo4j_session, {**common_job_parameters, "account_id": account_id})


@timeit
def get_applications(client: Cloudflare, account_id: str) -> list[dict[str, Any]]:
    # Iterating the SDK page fetches successive pages automatically. JSON mode
    # normalizes SDK datetime values while preserving provider field names.
    return [
        application.to_dict(mode="json")
        for application in client.zero_trust.access.applications.list(
            account_id=account_id
        )
    ]


def hostname_pattern(domain: str) -> str | None:
    """Normalize a public Access hostname while retaining label-scoped wildcards.

    Paths remain in public_domains on the application. This function does not
    evaluate paths or application precedence and never returns an access verdict.
    """
    try:
        parsed = urlsplit(domain if "://" in domain else "//" + domain)
        if (
            parsed.scheme not in ("", "http", "https")
            or parsed.username
            or parsed.password
            or parsed.port is not None
            or parsed.query
            or parsed.fragment
        ):
            return None
        host = (
            (parsed.hostname or "")
            .removesuffix(".")
            .encode("idna")
            .decode("ascii")
            .lower()
        )
    except (ValueError, UnicodeError):
        return None
    if len(host) > 253:
        return None
    try:
        ipaddress.ip_address(host)
        return None
    except ValueError:
        pass
    labels = host.split(".")
    if len(labels) < 2 or any(
        not re.fullmatch(r"[a-z0-9*](?:[a-z0-9*\-]{0,61}[a-z0-9*])?", label)
        or label.count("*") > 1
        for label in labels
    ):
        return None
    return host


def public_domains(application: dict[str, Any]) -> list[str]:
    """Read public destinations only, never SaaS/bookmark URLs or private hosts."""
    if application.get("type") != "self_hosted":
        return []
    # Newer APIs expose authoritative destinations, with legacy fields retained
    # for compatibility. An explicit empty/private-only destinations list must
    # not resurrect a stale legacy domain.
    if application.get("destinations") is not None:
        values = [
            destination.get("uri")
            for destination in application["destinations"]
            if destination.get("type", "public") == "public"
        ]
    else:
        values = [
            application.get("domain"),
            *(application.get("self_hosted_domains") or []),
        ]
    return sorted(
        {
            value
            for value in values
            if isinstance(value, str) and hostname_pattern(value)
        }
    )


def transform_applications(
    applications: list[dict[str, Any]],
    account_id: str,
    zones: list[dict[str, Any]] | None = None,
    records: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    zone_names = [(zone["id"], hostname_pattern(zone["name"])) for zone in zones or []]
    record_names = [
        (record["id"], hostname_pattern(record["name"])) for record in records or []
    ]
    result = []
    for application in applications:
        domains = public_domains(application)
        zone_ids: set[str] = set()
        dns_record_ids: set[str] = set()
        for domain in domains:
            host = hostname_pattern(domain)
            assert host is not None  # public_domains already validated it.
            # A delegated child zone wins over its parent; suffix matches need a
            # label boundary so notexample.com never belongs to example.com.
            matching_zones = [
                (zone_id, name)
                for zone_id, name in zone_names
                if name
                and "*" not in name
                and (host == name or host.endswith("." + name))
            ]
            if matching_zones:
                zone_ids.add(
                    max(matching_zones, key=lambda zone: len(zone[1] or ""))[0]
                )
            # Access wildcards match inside one label, unlike DNS wildcards.
            # Do not expand wildcard DNS records: DNS precedence/empty nonterminal
            # rules cannot be established by comparing two wildcard strings.
            matcher = re.compile("^" + re.escape(host).replace(r"\*", "[^.]*") + "$")
            dns_record_ids.update(
                record_id
                for record_id, name in record_names
                if name and "*" not in name and matcher.fullmatch(name)
            )
        result.append(
            {
                **application,
                "id": f"{account_id}/{application['id']}",
                "application_id": application["id"],
                "public_domains": domains,
                "zone_ids": sorted(zone_ids),
                "dns_record_ids": sorted(dns_record_ids),
            }
        )
    return result


def transform_policies(
    policies: list[dict[str, Any]], account_id: str, application_id: str
) -> list[dict[str, Any]]:
    result = []
    for policy in policies:
        row = {
            **policy,
            "id": f"{account_id}/{application_id}/{policy['id']}",
            "policy_id": policy["id"],
            "application_id": f"{account_id}/{application_id}",
        }
        for field in ("include", "require", "exclude"):
            value = policy.get(field)
            row[field] = (
                json.dumps(value, sort_keys=True) if value is not None else None
            )
        result.append(row)
    return result


def load_applications(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        CloudflareAccessApplicationSchema(),
        data,
        lastupdated=update_tag,
        account_id=account_id,
    )


def load_policies(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        CloudflareAccessPolicySchema(),
        data,
        lastupdated=update_tag,
        account_id=account_id,
    )


def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    # Both schemas are scoped to the account, so cleanup runs only after all
    # applications have loaded. Remove stale attachments before applications.
    GraphJob.from_node_schema(
        CloudflareAccessPolicySchema(), common_job_parameters
    ).run(
        neo4j_session,
    )
    GraphJob.from_node_schema(
        CloudflareAccessApplicationSchema(), common_job_parameters
    ).run(
        neo4j_session,
    )
