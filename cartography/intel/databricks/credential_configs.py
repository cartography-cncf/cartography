import re
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.databricks._account_scope import account_scoped_id
from cartography.intel.databricks.util import DatabricksAccountClient
from cartography.intel.databricks.util import epoch_ms_to_datetime
from cartography.models.databricks.credential_config import (
    DatabricksCredentialConfigSchema,
)
from cartography.util import timeit

# IAM role ARNs embed the owning 12-digit AWS account id as the 5th
# colon-separated field: arn:<partition>:iam::123456789012:role/name. The
# partition segment is left permissive (aws, aws-us-gov, aws-cn) so GovCloud /
# China role ARNs still link to their AWSAccount.
_AWS_ACCOUNT_ID_RE = re.compile(r"^arn:[^:]+:iam::(\d{12}):")


def _aws_account_id_from_arn(arn: str | None) -> str | None:
    if not arn:
        return None
    match = _AWS_ACCOUNT_ID_RE.match(arn)
    return match.group(1) if match else None


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: DatabricksAccountClient,
    account_id: str,
    common_job_parameters: dict[str, Any],
) -> None:
    configs = get(api_session)
    transformed = transform(configs, account_id)
    load_credential_configs(
        neo4j_session, transformed, account_id, common_job_parameters["UPDATE_TAG"]
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(api_session: DatabricksAccountClient) -> list[dict[str, Any]]:
    return api_session.get(api_session.account_uri("/credentials")) or []


@timeit
def transform(configs: list[dict[str, Any]], account_id: str) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for c in configs:
        credentials_id = c["credentials_id"]
        role_arn = ((c.get("aws_credentials") or {}).get("sts_role") or {}).get(
            "role_arn"
        )
        result.append(
            {
                "id": account_scoped_id(account_id, credentials_id),
                "credentials_id": credentials_id,
                "credentials_name": c.get("credentials_name"),
                "aws_role_arn": role_arn,
                "aws_account_id": _aws_account_id_from_arn(role_arn),
                "created_time": epoch_ms_to_datetime(c.get("creation_time")),
            }
        )
    return result


@timeit
def load_credential_configs(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        DatabricksCredentialConfigSchema(),
        data,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(
        DatabricksCredentialConfigSchema(), common_job_parameters
    ).run(neo4j_session)
