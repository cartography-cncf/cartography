import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.databricks._account_scope import account_scoped_id
from cartography.intel.databricks.util import DatabricksAccountClient
from cartography.models.databricks.account_user import DatabricksAccountUserSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


def _primary_email(emails: list[dict[str, Any]] | None) -> str | None:
    if not emails:
        return None
    for entry in emails:
        if entry.get("primary"):
            return entry.get("value")
    return emails[0].get("value")


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: DatabricksAccountClient,
    account_id: str,
    common_job_parameters: dict[str, Any],
) -> None:
    users = get(api_session)
    transformed = transform(users, account_id)
    load_users(
        neo4j_session, transformed, account_id, common_job_parameters["UPDATE_TAG"]
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(api_session: DatabricksAccountClient) -> list[dict[str, Any]]:
    return api_session.scim_list(api_session.account_uri("/scim/v2/Users"))


@timeit
def transform(users: list[dict[str, Any]], account_id: str) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for u in users:
        scim_id = u.get("id")
        # A blank SCIM id would collapse to the account-scoped key
        # "{account_id}/" and merge distinct malformed records onto one node;
        # skip rather than corrupt graph identity.
        if not scim_id:
            logger.warning("Skipping Databricks account user with empty SCIM id.")
            continue
        result.append(
            {
                "id": account_scoped_id(account_id, scim_id),
                "scim_id": scim_id,
                "user_name": u.get("userName"),
                "display_name": u.get("displayName"),
                "external_id": u.get("externalId"),
                "active": u.get("active"),
                "email": _primary_email(u.get("emails")),
                "group_ids": [
                    account_scoped_id(account_id, g["value"])
                    for g in (u.get("groups") or [])
                    if g.get("value")
                ],
            }
        )
    return result


@timeit
def load_users(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        DatabricksAccountUserSchema(),
        data,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(DatabricksAccountUserSchema(), common_job_parameters).run(
        neo4j_session
    )
