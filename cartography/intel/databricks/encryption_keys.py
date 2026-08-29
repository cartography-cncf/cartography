from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.databricks._account_scope import account_scoped_id
from cartography.intel.databricks.util import DatabricksAccountClient
from cartography.models.databricks.encryption_key import DatabricksEncryptionKeySchema
from cartography.util import timeit


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: DatabricksAccountClient,
    account_id: str,
    common_job_parameters: dict[str, Any],
) -> None:
    keys = get(api_session)
    transformed = transform(keys, account_id)
    load_encryption_keys(
        neo4j_session, transformed, account_id, common_job_parameters["UPDATE_TAG"]
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(api_session: DatabricksAccountClient) -> list[dict[str, Any]]:
    return api_session.get(api_session.account_uri("/customer-managed-keys")) or []


@timeit
def transform(keys: list[dict[str, Any]], account_id: str) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for k in keys:
        cmk_id = k["customer_managed_key_id"]
        aws_key = k.get("aws_key_info") or {}
        gcp_key = k.get("gcp_key_info") or {}
        result.append(
            {
                "id": account_scoped_id(account_id, cmk_id),
                "customer_managed_key_id": cmk_id,
                "use_cases": k.get("use_cases") or [],
                "aws_key_arn": aws_key.get("key_arn"),
                "aws_key_alias": aws_key.get("key_alias"),
                "gcp_kms_key_name": gcp_key.get("kms_key_id"),
            }
        )
    return result


@timeit
def load_encryption_keys(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        DatabricksEncryptionKeySchema(),
        data,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(
        DatabricksEncryptionKeySchema(), common_job_parameters
    ).run(neo4j_session)
