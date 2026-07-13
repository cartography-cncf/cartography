from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.databricks._account_scope import account_scoped_id
from cartography.intel.databricks.util import DatabricksAccountClient
from cartography.models.databricks.private_access_settings import (
    DatabricksPrivateAccessSettingsSchema,
)
from cartography.util import timeit


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: DatabricksAccountClient,
    account_id: str,
    common_job_parameters: dict[str, Any],
) -> None:
    settings = get(api_session)
    transformed = transform(settings, account_id)
    load_private_access_settings(
        neo4j_session, transformed, account_id, common_job_parameters["UPDATE_TAG"]
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(api_session: DatabricksAccountClient) -> list[dict[str, Any]]:
    return api_session.get(api_session.account_uri("/private-access-settings")) or []


@timeit
def transform(settings: list[dict[str, Any]], account_id: str) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for s in settings:
        pas_id = s["private_access_settings_id"]
        result.append(
            {
                "id": account_scoped_id(account_id, pas_id),
                "private_access_settings_id": pas_id,
                "private_access_settings_name": s.get("private_access_settings_name"),
                "public_access_enabled": s.get("public_access_enabled"),
                "private_access_level": s.get("private_access_level"),
                "region": s.get("region"),
            }
        )
    return result


@timeit
def load_private_access_settings(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        DatabricksPrivateAccessSettingsSchema(),
        data,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(
        DatabricksPrivateAccessSettingsSchema(), common_job_parameters
    ).run(neo4j_session)
