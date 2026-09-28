import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.netlify.util import get_list
from cartography.intel.netlify.util import paginated_get
from cartography.models.netlify.dnsrecord import NetlifyDNSRecordSchema
from cartography.models.netlify.dnszone import NetlifyDNSZoneSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

# Keys lifted off the domain registration object onto the zone, mapped to the property they land
# in. `auth_code` is deliberately absent: it is the EPP transfer authorization code, so ingesting
# it would put a domain-takeover credential in the graph. `renewal_price`, `failure_reason`,
# `transferred_at`, `deleted` and `auto_renew_at` are dropped as well; they add no signal that
# `status` and `expires_at` do not already carry.
_DOMAIN_REGISTRATION_FIELDS = {
    "registered_at": "domain_registered_at",
    "expires_at": "domain_expires_at",
    "auto_renew": "domain_auto_renew",
    "status": "domain_registration_status",
}


@timeit
def sync_netlify_dns(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    base_url: str,
    account_id: str,
    account_slug: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    zones = transform_netlify_dns_zones(
        get_netlify_dns_zones(api_session, base_url, account_slug),
    )
    records = []
    for zone in zones:
        records.extend(get_netlify_dns_records(api_session, base_url, zone["id"]))
    transformed_records = transform_netlify_dns_records(records)

    load_netlify_dns_zones(neo4j_session, zones, account_id, update_tag)
    load_netlify_dns_records(
        neo4j_session,
        transformed_records,
        account_id,
        update_tag,
    )
    cleanup_netlify_dns(neo4j_session, common_job_parameters)


@timeit
def get_netlify_dns_zones(
    api_session: requests.Session,
    base_url: str,
    account_slug: str,
) -> list[dict[str, Any]]:
    """
    Fetch the DNS zones of one team.

    The endpoint returns every zone the token can see unless it is filtered, so the team slug is
    passed explicitly: without it a token with access to several teams would pull another team's
    zones into this team's cleanup scope and then delete them.
    """
    return paginated_get(
        api_session,
        f"{base_url}/dns_zones",
        params={"account_slug": account_slug},
    )


@timeit
def get_netlify_dns_records(
    api_session: requests.Session,
    base_url: str,
    zone_id: str,
) -> list[dict[str, Any]]:
    return get_list(api_session, f"{base_url}/dns_zones/{zone_id}/dns_records")


def transform_netlify_dns_zones(
    zones: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Normalize `domain` to a string and flatten the domain registration onto the zone.

    The API documents `domain` as a string, and that is what a zone whose apex domain is
    registered elsewhere and delegated to Netlify DNS returns. A domain bought through Netlify
    carries the whole domain registration object there instead, which Neo4j cannot store as a
    property value.

    Only the renewal fields are kept: a domain close to expiry, with auto-renew off, or with a
    failed payment is a hijack candidate.
    """
    transformed = []
    for zone in zones:
        domain = zone.get("domain")
        registration: dict[str, Any] = {}
        # Every object-shaped `domain` takes this branch, including an empty or partial one:
        # falling back to the raw value for those would put the map back into the property.
        if isinstance(domain, dict):
            registration = domain
            domain = registration.get("name")
        transformed.append(
            {
                **zone,
                "domain": domain,
                # Copied field by field rather than spread: the registration carries its own
                # `id`, `name`, `account_id`, `user_id`, `created_at` and `updated_at`, which
                # would otherwise overwrite the zone's.
                **{
                    prop: registration.get(key)
                    for key, prop in _DOMAIN_REGISTRATION_FIELDS.items()
                },
            },
        )
    return transformed


def transform_netlify_dns_records(
    records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Copy `hostname` to `name`, which is what the DNSRecord ontology mapping requires.
    """
    return [{**record, "name": record.get("hostname")} for record in records]


@timeit
def load_netlify_dns_zones(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        NetlifyDNSZoneSchema(),
        data,
        lastupdated=update_tag,
        NETLIFY_ACCOUNT_ID=account_id,
    )


@timeit
def load_netlify_dns_records(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        NetlifyDNSRecordSchema(),
        data,
        lastupdated=update_tag,
        NETLIFY_ACCOUNT_ID=account_id,
    )


@timeit
def cleanup_netlify_dns(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    # Records before zones: a record hangs off its zone, so removing the zone first would strip
    # the edge that identifies the orphan.
    GraphJob.from_node_schema(NetlifyDNSRecordSchema(), common_job_parameters).run(
        neo4j_session,
    )
    GraphJob.from_node_schema(NetlifyDNSZoneSchema(), common_job_parameters).run(
        neo4j_session,
    )
