import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.huntress.util import get_paginated_huntress_items
from cartography.intel.huntress.util import required_id
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


def _scope_object(membership: dict[str, Any], key: str) -> dict[str, Any] | None:
    """Return a membership's `account` or `organization` object, or None when unset.

    A field that is present but not an object is rejected rather than read as "unset":
    treating a malformed `organization` as absent would fall through to the account
    branch and widen an organization grant into an account-wide role.
    """
    value = membership.get(key)
    if value is None or isinstance(value, dict):
        return value
    raise ValueError(
        f"Huntress returned membership {membership.get('id')!r} whose {key} scope is "
        f"not an object: {value!r}",
    )


def _membership_scope(
    membership: dict[str, Any],
    account_id: int,
) -> tuple[str, int]:
    """Resolve which scope a membership grants its permission label over.

    A membership is scoped to the account or to exactly one organization, never both and
    never neither. Both objects are validated rather than inferring "account" from a
    missing organization id: a malformed organization object would otherwise widen an
    organization grant into an account-wide role, which reads in the graph as more access
    than the user actually has.
    """
    account = _scope_object(membership, "account")
    organization = _scope_object(membership, "organization")

    if account is not None and organization is not None:
        raise ValueError(
            f"Huntress returned membership {membership.get('id')!r} scoped to both "
            "an account and an organization",
        )

    if organization is not None:
        return "org", required_id(organization, "membership organization")

    if account is None:
        raise ValueError(
            f"Huntress returned membership {membership.get('id')!r} scoped to neither "
            "an account nor an organization",
        )

    resolved_account_id = required_id(account, "membership account")
    if resolved_account_id != account_id:
        raise ValueError(
            f"Huntress returned membership {membership.get('id')!r} scoped to account "
            f"{resolved_account_id}, which is not the account being synced ({account_id})",
        )
    return "account", resolved_account_id


def transform(
    api_result: list[dict[str, Any]],
    account_id: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Derive the console users and the roles granted to them from flat membership records.

    Huntress has no role object: each membership carries a bare permission label scoped to
    either the account or one organization. Roles are therefore synthesized and deduped
    here, and a user's memberships are folded into one node per user.
    """
    users: dict[int, dict[str, Any]] = {}
    roles: dict[str, dict[str, Any]] = {}

    for membership in api_result:
        user = membership.get("user")
        # Every membership documents a user. A malformed one is not skipped: skipping it
        # would leave that user out of the load while the cleanup below still runs,
        # silently deleting a console user a previous sync had ingested.
        if not isinstance(user, dict):
            raise ValueError(
                f"Huntress returned membership {membership.get('id')!r} with no user object",
            )
        user_id = required_id(user, "membership user")

        scope, scope_id = _membership_scope(membership, account_id)
        organization_id = scope_id if scope == "org" else None

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
        # The scope type is part of the id. Account and organization ids come from
        # separate Huntress sequences, so the numbers can collide; without the prefix,
        # account 42 and organization 42 would collapse onto one role node and hand
        # every holder of one grant the other one's scope.
        role_id = f"{scope}/{scope_id}/{permissions}"
        roles.setdefault(
            role_id,
            {
                "id": role_id,
                "name": permissions,
                "scope": scope,
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
