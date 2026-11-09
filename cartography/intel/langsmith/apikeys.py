import logging
from collections import Counter
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.intel.langsmith.util import cleanup_if_complete
from cartography.intel.langsmith.util import LangSmithClient
from cartography.intel.langsmith.util import LangSmithFetchError
from cartography.intel.langsmith.util import org_scoped_id
from cartography.intel.langsmith.util import resolve_ls_user_id
from cartography.models.langsmith.apikey import LangSmithApiKeySchema
from cartography.models.langsmith.serviceaccount import LangSmithServiceAccountSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: LangSmithClient,
    org_id: str,
    user_lookup: dict[str, str],
    workspaces: list[dict[str, Any]],
    common_job_parameters: dict[str, Any],
) -> None:
    service_accounts, service_accounts_complete = get_service_accounts(client, org_id)

    keys: list[dict[str, Any]] = []
    keys_complete = True
    for key_type in ("service_key", "pat", "scim_token"):
        rows, ok = _fetch_optional(client, org_id, key_type)
        keys.extend(rows)
        keys_complete = keys_complete and ok
    for workspace in workspaces:
        rows, ok = _fetch_workspace_keys(client, org_id, workspace["id"])
        keys.extend(rows)
        keys_complete = keys_complete and ok

    transformed = transform_keys(keys, user_lookup, workspaces, org_id)
    load_api_keys(
        neo4j_session,
        service_accounts,
        transformed,
        org_id,
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup_if_complete(
        neo4j_session, LangSmithApiKeySchema(), keys_complete, common_job_parameters
    )
    cleanup_if_complete(
        neo4j_session,
        LangSmithServiceAccountSchema(),
        service_accounts_complete,
        common_job_parameters,
    )


_ORG_KEY_SOURCES = {
    "service_key": "/api/v1/orgs/current/service-keys",
    "pat": "/api/v1/orgs/current/members/personal-access-tokens",
    "scim_token": "/api/v1/platform/orgs/current/scim/tokens",
}


def _fetch_optional(
    client: LangSmithClient, org_id: str, key_type: str
) -> tuple[list[dict[str, Any]], bool]:
    """
    Fetch one organization-scoped credential listing, tolerating a missing permission.

    Listing every member's personal access tokens needs organization:pats:read, which a
    credential may legitimately lack. Losing that listing should narrow the graph, not fail
    the module.
    """
    path = _ORG_KEY_SOURCES[key_type]
    try:
        rows = client.get(path, org_id=org_id)
    except LangSmithFetchError as err:
        logger.warning("Skipping LangSmith %s inventory: %s", key_type, err)
        # A 404 means the feature is off for this organization (for example SCIM), so
        # there is nothing to list; only a hidden listing is incomplete.
        return [], err.not_found
    for row in rows:
        row["key_type"] = key_type
    return rows, True


def _fetch_workspace_keys(
    client: LangSmithClient, org_id: str, workspace_id: str
) -> tuple[list[dict[str, Any]], bool]:
    try:
        rows = client.get("/api/v1/api-key", org_id=org_id, tenant_id=workspace_id)
    except LangSmithFetchError as err:
        logger.warning(
            "Skipping LangSmith API keys for workspace %s: %s", workspace_id, err
        )
        return [], err.not_found
    for row in rows:
        row["key_type"] = "workspace_key"
        row["workspace_id"] = workspace_id
    return rows, True


@timeit
def get_service_accounts(
    client: LangSmithClient, org_id: str
) -> tuple[list[dict[str, Any]], bool]:
    try:
        return client.get("/api/v1/service-accounts", org_id=org_id), True
    except LangSmithFetchError as err:
        logger.warning("Skipping LangSmith service accounts: %s", err)
        return [], err.not_found


def transform_keys(
    keys: list[dict[str, Any]],
    user_lookup: dict[str, str],
    workspaces: list[dict[str, Any]],
    org_id: str,
) -> list[dict[str, Any]]:
    """Shape credentials for ingest. Only the non-secret short prefix is retained."""
    # Keys name their default workspace by display name only. Display names are not
    # unique, so an ambiguous name links to no workspace rather than to the wrong one.
    name_counts = Counter(
        workspace["display_name"]
        for workspace in workspaces
        if workspace.get("display_name")
    )
    workspace_by_name = {
        workspace["display_name"]: workspace["id"]
        for workspace in workspaces
        if name_counts[workspace.get("display_name")] == 1
    }

    transformed = []
    for key in keys:
        owner_ls_user_id = resolve_ls_user_id(key.get("created_by"), user_lookup)

        workspace_id = key.get("workspace_id")
        if not workspace_id and key.get("default_workspace_name"):
            workspace_id = workspace_by_name.get(key["default_workspace_name"])

        role_ids = [
            org_scoped_id(org_id, role_id)
            for role_id in (key.get("role_id"), key.get("org_role_id"))
            if role_id
        ]

        transformed.append(
            {
                "id": key["id"],
                # SCIM tokens report their prefix as short_token rather than short_key.
                "short_key": key.get("short_key") or key.get("short_token"),
                "description": key.get("description"),
                "key_type": key["key_type"],
                "access_scope": key.get("access_scope"),
                "read_only": key.get("read_only"),
                "created_at": key.get("created_at"),
                "last_used_at": key.get("last_used_at"),
                "expires_at": key.get("expires_at"),
                "revoked_at": key.get("revoked_at"),
                "workspace_names": key.get("workspace_names") or [],
                "default_workspace_name": key.get("default_workspace_name"),
                "owner_ls_user_id": owner_ls_user_id,
                "workspace_id": workspace_id,
                "role_ids": role_ids,
            }
        )
    return transformed


@timeit
def load_api_keys(
    neo4j_session: neo4j.Session,
    service_accounts: list[dict[str, Any]],
    keys: list[dict[str, Any]],
    org_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        LangSmithServiceAccountSchema(),
        service_accounts,
        lastupdated=update_tag,
        ORG_ID=org_id,
    )
    load(
        neo4j_session,
        LangSmithApiKeySchema(),
        keys,
        lastupdated=update_tag,
        ORG_ID=org_id,
    )
