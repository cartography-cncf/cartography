from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any
from urllib.parse import urlsplit

import neo4j

from cartography.client.core.tx import load_matchlinks
from cartography.client.core.tx import read_list_of_dicts_tx
from cartography.graph.job import GraphJob
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.okta.federation import (
    OktaApplicationToGitHubOrganizationMatchLink,
)
from cartography.models.okta.federation import (
    OktaApplicationToGoogleWorkspaceTenantMatchLink,
)
from cartography.models.okta.federation import (
    OktaApplicationToSalesforceOrganizationMatchLink,
)
from cartography.models.okta.federation import OktaApplicationToSlackTeamMatchLink
from cartography.util import timeit

logger = logging.getLogger(__name__)

_FEDERATION_SCHEMAS: tuple[tuple[str, CartographyRelSchema], ...] = (
    ("SlackTeam", OktaApplicationToSlackTeamMatchLink()),
    ("GitHubOrganization", OktaApplicationToGitHubOrganizationMatchLink()),
    ("GoogleWorkspaceTenant", OktaApplicationToGoogleWorkspaceTenantMatchLink()),
    ("SalesforceOrganization", OktaApplicationToSalesforceOrganizationMatchLink()),
)


def _index_targets(
    targets: list[dict[str, Any]],
    key_field: str,
) -> dict[str, list[str]]:
    index: dict[str, list[str]] = defaultdict(list)
    for target in targets:
        target_id = target.get("id")
        key = target.get(key_field)
        if target_id and isinstance(key, str) and key:
            index[key.lower()].append(target_id)
    return index


def _extract_host(url: Any) -> str | None:
    if not isinstance(url, str) or not url:
        return None
    try:
        host = urlsplit(url).hostname
    except ValueError:
        # Login URLs are typed by admins; a malformed one must not stop the sync.
        return None
    return host.lower() if host else None


def _salesforce_custom_domain_candidates(
    sf_by_host: dict[str, list[dict[str, Any]]],
    custom_domain: str,
    instance_type: Any,
) -> list[dict[str, Any]]:
    domain = custom_domain.lower()
    if instance_type == "SANDBOX":
        # Sandbox My Domain hosts are <domain>--<sandbox>.sandbox.my.salesforce.com;
        # admins may enter either the base domain or <domain>--<sandbox> in customDomain.
        exact = f"{domain}.sandbox.my.salesforce.com"
        prefix = f"{domain}--"
        return [
            org
            for host, orgs in sf_by_host.items()
            if host == exact
            or (host.startswith(prefix) and host.endswith(".sandbox.my.salesforce.com"))
            for org in orgs
        ]
    return sf_by_host.get(f"{domain}.my.salesforce.com", [])


def _index_salesforce_orgs_by_host(
    salesforce_orgs: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    index: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for org in salesforce_orgs:
        org_id = org.get("id")
        host = _extract_host(org.get("instance_url"))
        if org_id and host:
            index[host].append(org)
    return index


def _salesforce_instance_type_matches(
    instance_type: Any,
    is_sandbox: Any,
) -> bool:
    if instance_type == "PRODUCTION" and is_sandbox is True:
        return False
    if instance_type == "SANDBOX" and is_sandbox is False:
        return False
    return True


def resolve_okta_federation_links(
    okta_apps: list[dict[str, Any]],
    slack_teams: list[dict[str, Any]],
    github_orgs: list[dict[str, Any]],
    google_tenants: list[dict[str, Any]],
    salesforce_orgs: list[dict[str, Any]] | None = None,
) -> dict[str, list[dict[str, Any]]]:
    """
    Resolve Okta catalog applications to matching SaaS tenant nodes in memory.

    Returns a mapping from target node label (``SlackTeam``, ``GitHubOrganization``,
    ``GoogleWorkspaceTenant``, ``SalesforceOrganization``) to MatchLink row dicts.
    """
    slack_by_domain = _index_targets(slack_teams, "domain")
    slack_by_enterprise_domain = _index_targets(slack_teams, "enterprise_domain")
    github_by_username = _index_targets(github_orgs, "username")
    google_by_domain = _index_targets(google_tenants, "domain")
    sf_by_host = _index_salesforce_orgs_by_host(salesforce_orgs or [])

    links: dict[str, list[dict[str, Any]]] = {
        "SlackTeam": [],
        "GitHubOrganization": [],
        "GoogleWorkspaceTenant": [],
        "SalesforceOrganization": [],
    }

    for app in okta_apps:
        app_id = app.get("id")
        app_name = app.get("name")
        if not app_id or not app_name:
            continue

        # An inactive app does not sign anyone in. Status is None only for rows
        # that predate the status property.
        if app.get("status") not in (None, "ACTIVE"):
            continue

        sign_on_mode = app.get("sign_on_mode")

        if app_name == "slack":
            domain = app.get("settings_app_domain")
            if not isinstance(domain, str) or not domain:
                continue
            domain_lower = domain.lower()
            if domain_lower.endswith(".enterprise"):
                enterprise_domain = domain_lower[: -len(".enterprise")]
                if not enterprise_domain:
                    continue
                target_ids = slack_by_enterprise_domain.get(enterprise_domain, [])
            else:
                matches = slack_by_domain.get(domain_lower, [])
                target_ids = matches if len(matches) == 1 else []
            matched_on = "settings.app.domain"
            target_label = "SlackTeam"

        elif app_name == "githubcloud":
            github_org = app.get("settings_app_github_org")
            if not isinstance(github_org, str) or not github_org:
                continue
            matches = github_by_username.get(github_org.lower(), [])
            target_ids = matches if len(matches) == 1 else []
            matched_on = "settings.app.githubOrg"
            target_label = "GitHubOrganization"

        elif app_name == "google":
            domain = app.get("settings_app_domain")
            if not isinstance(domain, str) or not domain:
                continue
            matches = google_by_domain.get(domain.lower(), [])
            target_ids = matches if len(matches) == 1 else []
            matched_on = "settings.app.domain"
            target_label = "GoogleWorkspaceTenant"

        elif app_name == "salesforce":
            login_host = _extract_host(app.get("settings_app_login_url"))
            custom_domain = app.get("settings_app_custom_domain")
            instance_type = app.get("settings_app_instance_type")
            if login_host and login_host in sf_by_host:
                candidates = sf_by_host[login_host]
                matched_on = "settings.app.loginUrl"
            elif isinstance(custom_domain, str) and custom_domain:
                candidates = _salesforce_custom_domain_candidates(
                    sf_by_host, custom_domain, instance_type
                )
                matched_on = "settings.app.customDomain"
            else:
                continue

            filtered = [
                org
                for org in candidates
                if _salesforce_instance_type_matches(
                    instance_type, org.get("is_sandbox")
                )
            ]
            target_ids = [org["id"] for org in filtered] if len(filtered) == 1 else []
            target_label = "SalesforceOrganization"

        else:
            continue

        for target_id in target_ids:
            links[target_label].append(
                {
                    "okta_app_id": app_id,
                    "target_id": target_id,
                    "sign_on_mode": sign_on_mode,
                    "matched_on": matched_on,
                },
            )

    return links


def _get_okta_federation_apps(
    neo4j_session: neo4j.Session,
    okta_org_id: str,
) -> list[dict[str, Any]]:
    query = """
    MATCH (:OktaOrganization {id: $okta_org_id})-[:RESOURCE]->(app:OktaApplication)
    WHERE app.name IN ['slack', 'githubcloud', 'google', 'salesforce']
    RETURN app.id AS id,
           app.name AS name,
           app.status AS status,
           app.sign_on_mode AS sign_on_mode,
           app.settings_app_domain AS settings_app_domain,
           app.settings_app_github_org AS settings_app_github_org,
           app.settings_app_login_url AS settings_app_login_url,
           app.settings_app_instance_type AS settings_app_instance_type,
           app.settings_app_custom_domain AS settings_app_custom_domain
    """
    return neo4j_session.execute_read(
        read_list_of_dicts_tx,
        query,
        okta_org_id=okta_org_id,
    )


def _get_candidate_slack_teams(neo4j_session: neo4j.Session) -> list[dict[str, Any]]:
    query = """
    MATCH (t:SlackTeam)
    RETURN t.id AS id,
           t.domain AS domain,
           t.enterprise_domain AS enterprise_domain
    """
    return neo4j_session.execute_read(read_list_of_dicts_tx, query)


def _get_candidate_github_orgs(neo4j_session: neo4j.Session) -> list[dict[str, Any]]:
    query = """
    MATCH (o:GitHubOrganization)
    RETURN o.id AS id,
           o.username AS username
    """
    return neo4j_session.execute_read(read_list_of_dicts_tx, query)


def _get_candidate_google_tenants(neo4j_session: neo4j.Session) -> list[dict[str, Any]]:
    query = """
    MATCH (t:GoogleWorkspaceTenant)
    RETURN t.id AS id,
           t.domain AS domain
    """
    return neo4j_session.execute_read(read_list_of_dicts_tx, query)


def _get_candidate_salesforce_orgs(
    neo4j_session: neo4j.Session,
) -> list[dict[str, Any]]:
    query = """
    MATCH (o:SalesforceOrganization)
    RETURN o.id AS id,
           o.instance_url AS instance_url,
           o.is_sandbox AS is_sandbox
    """
    return neo4j_session.execute_read(read_list_of_dicts_tx, query)


@timeit
def _load_okta_federation_links(
    neo4j_session: neo4j.Session,
    links_by_label: dict[str, list[dict[str, Any]]],
    okta_update_tag: int,
    okta_org_id: str,
) -> None:
    for label, schema in _FEDERATION_SCHEMAS:
        logger.info(
            "Loading %d Okta FEDERATES_TO relationships to %s nodes",
            len(links_by_label.get(label, [])),
            label,
        )
        load_matchlinks(
            neo4j_session,
            schema,
            links_by_label.get(label, []),
            lastupdated=okta_update_tag,
            _sub_resource_label="OktaOrganization",
            _sub_resource_id=okta_org_id,
        )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    okta_update_tag: int,
    okta_org_id: str,
) -> None:
    """Remove stale Okta application federation relationships."""
    for _, schema in _FEDERATION_SCHEMAS:
        GraphJob.from_matchlink(
            schema,
            "OktaOrganization",
            okta_org_id,
            okta_update_tag,
        ).run(neo4j_session)


@timeit
def sync_okta_federation(
    neo4j_session: neo4j.Session,
    okta_update_tag: int,
    okta_org_id: str,
) -> None:
    """
    Link Okta SSO catalog applications to the SaaS tenant nodes they sign users into.

    With the default module order, Okta syncs before GitHub, Salesforce, and Slack, so
    ``FEDERATES_TO`` links to ``GitHubOrganization``, ``SalesforceOrganization``, and
    ``SlackTeam`` nodes appear from the next sync after those nodes exist in the graph;
    Google Workspace syncs before Okta.
    """
    logger.info("Syncing Okta application federation links")
    okta_apps = _get_okta_federation_apps(neo4j_session, okta_org_id)
    slack_teams = _get_candidate_slack_teams(neo4j_session)
    github_orgs = _get_candidate_github_orgs(neo4j_session)
    google_tenants = _get_candidate_google_tenants(neo4j_session)
    salesforce_orgs = _get_candidate_salesforce_orgs(neo4j_session)

    links_by_label = resolve_okta_federation_links(
        okta_apps,
        slack_teams,
        github_orgs,
        google_tenants,
        salesforce_orgs,
    )
    _load_okta_federation_links(
        neo4j_session,
        links_by_label,
        okta_update_tag,
        okta_org_id,
    )
    cleanup(neo4j_session, okta_update_tag, okta_org_id)
