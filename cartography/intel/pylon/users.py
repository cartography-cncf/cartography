import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.pylon.util import paginated_get
from cartography.models.pylon.serviceaccount import PylonServiceAccountSchema
from cartography.models.pylon.user import PylonUserSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    base_url: str,
    common_job_parameters: dict[str, Any],
) -> None:
    raw_users = get(api_session, base_url)
    users, service_accounts = transform(raw_users)
    load_users(
        neo4j_session,
        users,
        common_job_parameters["ORG_ID"],
        common_job_parameters["UPDATE_TAG"],
    )
    load_service_accounts(
        neo4j_session,
        service_accounts,
        common_job_parameters["ORG_ID"],
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(api_session: requests.Session, base_url: str) -> list[dict[str, Any]]:
    return paginated_get(
        api_session,
        f"{base_url}/users",
        params={"include_deactivated": "true"},
    )


def transform(
    raw_users: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Split Pylon users into people and non-human identities.

    API tokens with their own identity and bots can't sign in, so Pylon returns
    them without an email address. Every entry without an email is treated as
    a service account.
    """
    users = []
    service_accounts = []
    for user in raw_users:
        # `role_id` is deprecated and returns only one of the user's roles.
        role_ids = user.get("role_ids")
        if role_ids is None:
            roles = user.get("roles")
            if roles is not None:
                role_ids = [role["id"] for role in roles]
            else:
                role_ids = [user["role_id"]] if user.get("role_id") else []
        identity = {
            "id": user["id"],
            "name": user.get("name"),
            "is_deactivated": user.get("is_deactivated"),
            "role_ids": sorted(role_ids),
        }
        email = user.get("email") or None
        if email is None:
            service_accounts.append(identity)
            continue
        identity["email"] = email
        identity["emails"] = user.get("emails") or []
        users.append(identity)
    return users, service_accounts


@timeit
def load_users(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    org_id: str,
    update_tag: int,
) -> None:
    logger.info("Loading %d Pylon users for organization %s", len(data), org_id)
    load(
        neo4j_session,
        PylonUserSchema(),
        data,
        lastupdated=update_tag,
        ORG_ID=org_id,
    )


@timeit
def load_service_accounts(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    org_id: str,
    update_tag: int,
) -> None:
    logger.info(
        "Loading %d Pylon service accounts for organization %s",
        len(data),
        org_id,
    )
    load(
        neo4j_session,
        PylonServiceAccountSchema(),
        data,
        lastupdated=update_tag,
        ORG_ID=org_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(PylonUserSchema(), common_job_parameters).run(
        neo4j_session,
    )
    GraphJob.from_node_schema(
        PylonServiceAccountSchema(),
        common_job_parameters,
    ).run(neo4j_session)
