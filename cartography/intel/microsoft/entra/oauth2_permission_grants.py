import logging
from collections import defaultdict
from typing import Any

import neo4j
from msgraph import GraphServiceClient
from msgraph.generated.models.o_auth2_permission_grant import OAuth2PermissionGrant

from cartography.client.core.tx import load_matchlinks
from cartography.client.core.tx import read_list_of_dicts_tx
from cartography.graph.job import GraphJob
from cartography.intel.microsoft import credentials
from cartography.intel.microsoft.entra.utils import (
    get_paginated_values_with_expired_page_retry,
)
from cartography.models.microsoft.entra.oauth2_permission_grant import (
    EntraTenantToServicePrincipalAdminConsentedMatchLink,
)
from cartography.models.microsoft.entra.oauth2_permission_grant import (
    EntraUserToServicePrincipalAuthorizedMatchLink,
)
from cartography.util import timeit

logger = logging.getLogger(__name__)

MICROSOFT_GRAPH_APP_ID = "00000003-0000-0000-c000-000000000000"
MICROSOFT_GRAPH_SCOPE_PREFIX = "https://graph.microsoft.com"


@timeit
async def get_oauth2_permission_grants(
    client: GraphServiceClient,
) -> list[OAuth2PermissionGrant]:
    return await get_paginated_values_with_expired_page_retry(
        client.oauth2_permission_grants.get,
        lambda url: client.oauth2_permission_grants.with_url(url).get(),
        "OAuth2 permission grants",
    )


def get_resource_app_ids(
    neo4j_session: neo4j.Session,
    tenant_id: str,
    resource_ids: list[str],
) -> dict[str, str]:
    """Map each granted API's service principal id to its app id, from the graph."""
    rows = neo4j_session.execute_read(
        read_list_of_dicts_tx,
        """
        MATCH (:AzureTenant {id: $tenant_id})-[:RESOURCE]->(sp:EntraServicePrincipal)
        WHERE sp.id IN $resource_ids AND sp.app_id IS NOT NULL
        RETURN sp.id AS id, sp.app_id AS app_id
        """,
        tenant_id=tenant_id,
        resource_ids=resource_ids,
    )
    return {row["id"]: row["app_id"] for row in rows}


def _qualify_scope(scope: str, resource_app_id: str) -> str:
    # A grant's scopes are bare names relative to the API it targets. Graph's are
    # requested in full as https://graph.microsoft.com/<name>, the same URL form
    # Google Workspace scopes take; any other API is named by its app id.
    if resource_app_id == MICROSOFT_GRAPH_APP_ID:
        return f"{MICROSOFT_GRAPH_SCOPE_PREFIX}/{scope}"
    return f"{resource_app_id}/{scope}"


def transform_oauth2_permission_grants(
    grants: list[OAuth2PermissionGrant],
    tenant_id: str,
    resource_app_ids: dict[str, str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """
    Fold grants into one AUTHORIZED edge per (user, app) and one ADMIN_CONSENTED edge
    per app, each carrying the union of its scopes.

    Graph returns one grant per (client, principal, API), so a user who consented to an
    app that calls both Graph and SharePoint has two grants for one authorization.
    """
    user_scopes: dict[tuple[str, str], set[str]] = defaultdict(set)
    admin_scopes: dict[str, set[str]] = defaultdict(set)
    for grant in grants:
        scopes = (grant.scope or "").split()
        if not grant.client_id or not grant.resource_id or not scopes:
            continue
        resource_app_id = resource_app_ids.get(grant.resource_id, grant.resource_id)
        qualified = {_qualify_scope(scope, resource_app_id) for scope in scopes}
        if grant.consent_type == "AllPrincipals":
            admin_scopes[grant.client_id] |= qualified
        elif grant.consent_type == "Principal" and grant.principal_id:
            user_scopes[(grant.principal_id, grant.client_id)] |= qualified

    authorizations = [
        {
            "principal_id": principal_id,
            "client_id": client_id,
            "scopes": sorted(scopes),
            "match_method": None,
        }
        for (principal_id, client_id), scopes in sorted(user_scopes.items())
    ]
    admin_consents = [
        {"tenant_id": tenant_id, "client_id": client_id, "scopes": sorted(scopes)}
        for client_id, scopes in sorted(admin_scopes.items())
    ]
    return authorizations, admin_consents


@timeit
def load_oauth2_permission_grants(
    neo4j_session: neo4j.Session,
    authorizations: list[dict[str, Any]],
    admin_consents: list[dict[str, Any]],
    tenant_id: str,
    update_tag: int,
) -> None:
    load_matchlinks(
        neo4j_session,
        EntraUserToServicePrincipalAuthorizedMatchLink(),
        authorizations,
        lastupdated=update_tag,
        _sub_resource_label="AzureTenant",
        _sub_resource_id=tenant_id,
    )
    load_matchlinks(
        neo4j_session,
        EntraTenantToServicePrincipalAdminConsentedMatchLink(),
        admin_consents,
        lastupdated=update_tag,
        _sub_resource_label="AzureTenant",
        _sub_resource_id=tenant_id,
    )


@timeit
def cleanup_oauth2_permission_grants(
    neo4j_session: neo4j.Session,
    tenant_id: str,
    update_tag: int,
) -> None:
    for matchlink in (
        EntraUserToServicePrincipalAuthorizedMatchLink(),
        EntraTenantToServicePrincipalAdminConsentedMatchLink(),
    ):
        GraphJob.from_matchlink(matchlink, "AzureTenant", tenant_id, update_tag).run(
            neo4j_session
        )


@timeit
async def sync_oauth2_permission_grants(
    neo4j_session: neo4j.Session,
    tenant_id: str,
    client_id: str | None,
    client_secret: str | None,
    update_tag: int,
    common_job_parameters: dict[str, Any],
    *,
    delegated_auth: bool = False,
    access_token: str | None = None,
) -> None:
    """Sync delegated consent grants. Runs after users and service principals, which they link."""
    credential = credentials.make_credential(
        tenant_id,
        client_id,
        client_secret,
        delegated_auth=delegated_auth,
        access_token=access_token,
    )
    client = GraphServiceClient(
        credential, scopes=["https://graph.microsoft.com/.default"]
    )

    grants = await get_oauth2_permission_grants(client)
    resource_app_ids = get_resource_app_ids(
        neo4j_session,
        tenant_id,
        sorted({grant.resource_id for grant in grants if grant.resource_id}),
    )
    authorizations, admin_consents = transform_oauth2_permission_grants(
        grants, tenant_id, resource_app_ids
    )
    logger.info(
        "Loading %d Entra user consents and %d admin consents from %d grants",
        len(authorizations),
        len(admin_consents),
        len(grants),
    )
    load_oauth2_permission_grants(
        neo4j_session, authorizations, admin_consents, tenant_id, update_tag
    )

    if not delegated_auth:
        cleanup_oauth2_permission_grants(neo4j_session, tenant_id, update_tag)
