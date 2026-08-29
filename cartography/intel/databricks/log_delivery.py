from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.databricks._account_scope import account_scoped_id
from cartography.intel.databricks.util import DatabricksAccountClient
from cartography.models.databricks.log_delivery import DatabricksLogDeliverySchema
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
    load_log_delivery(
        neo4j_session, transformed, account_id, common_job_parameters["UPDATE_TAG"]
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(api_session: DatabricksAccountClient) -> list[dict[str, Any]]:
    data = api_session.get(api_session.account_uri("/log-delivery")) or {}
    return data.get("log_delivery_configurations", []) or []


@timeit
def transform(configs: list[dict[str, Any]], account_id: str) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for c in configs:
        config_id = c["config_id"]
        # The bucket name is not returned inline; it lives on the referenced
        # storage configuration. Surface it when the API includes the resolved
        # config block, else leave null (the storage_configuration_id link is
        # still available via that resource's own node).
        s3_bucket_name = (
            (c.get("storage_configuration") or {}).get("root_bucket_info") or {}
        ).get("bucket_name")
        status = (c.get("status") or {}) if isinstance(c.get("status"), dict) else {}
        result.append(
            {
                "id": account_scoped_id(account_id, config_id),
                "config_id": config_id,
                "config_name": c.get("config_name"),
                "log_type": c.get("log_type"),
                "output_format": c.get("output_format"),
                "status": status.get("status") or c.get("status"),
                "s3_bucket_name": s3_bucket_name,
                "delivery_path_prefix": c.get("delivery_path_prefix"),
            }
        )
    return result


@timeit
def load_log_delivery(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        DatabricksLogDeliverySchema(),
        data,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(DatabricksLogDeliverySchema(), common_job_parameters).run(
        neo4j_session
    )
