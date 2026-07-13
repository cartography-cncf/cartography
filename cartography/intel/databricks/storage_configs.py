from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.databricks._account_scope import account_scoped_id
from cartography.intel.databricks.util import DatabricksAccountClient
from cartography.intel.databricks.util import epoch_ms_to_datetime
from cartography.models.databricks.storage_config import DatabricksStorageConfigSchema
from cartography.util import timeit


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: DatabricksAccountClient,
    account_id: str,
    common_job_parameters: dict[str, Any],
) -> None:
    configs = get(api_session)
    transformed = transform(configs, account_id)
    load_storage_configs(
        neo4j_session, transformed, account_id, common_job_parameters["UPDATE_TAG"]
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(api_session: DatabricksAccountClient) -> list[dict[str, Any]]:
    return api_session.get(api_session.account_uri("/storage-configurations")) or []


@timeit
def transform(configs: list[dict[str, Any]], account_id: str) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for c in configs:
        storage_configuration_id = c["storage_configuration_id"]
        result.append(
            {
                "id": account_scoped_id(account_id, storage_configuration_id),
                "storage_configuration_id": storage_configuration_id,
                "storage_configuration_name": c.get("storage_configuration_name"),
                "root_bucket_name": (c.get("root_bucket_info") or {}).get(
                    "bucket_name"
                ),
                "created_time": epoch_ms_to_datetime(c.get("creation_time")),
            }
        )
    return result


@timeit
def load_storage_configs(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        DatabricksStorageConfigSchema(),
        data,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(
        DatabricksStorageConfigSchema(), common_job_parameters
    ).run(neo4j_session)
