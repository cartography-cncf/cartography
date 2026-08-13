import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.huntress.util import get_paginated_huntress_items
from cartography.models.huntress.role import HuntressRoleSchema
from cartography.models.huntress.user import HuntressUserSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get(
    api_session: requests.Session,
    base_uri: str,
) -> list[dict[str, Any]] | None:
    """Fetch every console membership, or return None when the credentials cannot read them.

    Listing memberships needs a permission that Huntress does not grant to every API
    credential. Returning None rather than an empty list lets the caller skip BOTH the
    load and the cleanup: an empty list would look like a successful empty sync and delete
    every user and role ingested by a previous run that did have the permission.
    """
    try:
        return get_paginated_huntress_items(
            api_session,
            base_uri,
            "memberships",
            "memberships",
        )
    except requests.exceptions.HTTPError as e:
        if e.response is not None and e.response.status_code == 403:
            logger.warning(
                "Huntress API credentials are not authorized to list memberships. "
                "Skipping console users and roles.",
            )
            return None
        raise


def transform(
    api_result: list[dict[str, Any]],
    account_id: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Derive the console users and the roles granted to them from flat membership records.

    Huntress has no role object: each membership carries a bare permission label scoped to
    either the account or one organization. Roles are therefore synthesised and deduped
    here, and a user's memberships are folded into one node per user.
    """
    users: dict[Any, dict[str, Any]] = {}
    roles: dict[str, dict[str, Any]] = {}

    for membership in api_result:
        user = membership.get("user")
        if not isinstance(user, dict) or user.get("id") is None:
            logger.warning(
                "Huntress membership %s has no user attached; skipping it.",
                membership.get("id"),
            )
            continue

        organization = membership.get("organization")
        organization_id = (
            organization.get("id") if isinstance(organization, dict) else None
        )

        user_id = user["id"]
        entry = users.setdefault(
            user_id,
            {
                "id": user_id,
                "email": user.get("email"),
                "name": user.get("name"),
                "role_ids": set(),
                "organization_ids": set(),
            },
        )
        if organization_id is not None:
            entry["organization_ids"].add(organization_id)

        permissions = membership.get("permissions")
        if permissions is None:
            continue
        scope_id = organization_id if organization_id is not None else account_id
        role_id = f"{scope_id}/{permissions}"
        roles.setdefault(
            role_id,
            {
                "id": role_id,
                "name": permissions,
                "scope": "org" if organization_id is not None else "account",
                "organization_id": organization_id,
            },
        )
        entry["role_ids"].add(role_id)

    transformed_users = []
    for entry in users.values():
        transformed_users.append(
            {
                **entry,
                "role_ids": sorted(entry["role_ids"]),
                "organization_ids": sorted(entry["organization_ids"]),
            }
        )
    return transformed_users, list(roles.values())


def load_memberships(
    neo4j_session: neo4j.Session,
    users: list[dict[str, Any]],
    roles: list[dict[str, Any]],
    account_id: int,
    update_tag: int,
) -> None:
    # Roles first: the users carry the HAS_ROLE edges, which only match existing nodes.
    load(
        neo4j_session,
        HuntressRoleSchema(),
        roles,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )
    load(
        neo4j_session,
        HuntressUserSchema(),
        users,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )


def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(HuntressUserSchema(), common_job_parameters).run(
        neo4j_session,
    )
    GraphJob.from_node_schema(HuntressRoleSchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    base_uri: str,
    account_id: int,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    raw_data = get(api_session, base_uri)
    if raw_data is None:
        return
    users, roles = transform(raw_data, account_id)
    load_memberships(neo4j_session, users, roles, account_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)
