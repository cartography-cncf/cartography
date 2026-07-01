from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.databricks.util import DatabricksWorkspaceClient
from cartography.intel.databricks.util import epoch_ms_to_datetime
from cartography.intel.databricks.util import uc_id
from cartography.models.databricks.storage_credential import (
    DatabricksStorageCredentialSchema,
)
from cartography.util import timeit


def _credential_type(cred: dict[str, Any]) -> str | None:
    """Derive a single credential type from the mutually-exclusive cloud blocks."""
    if cred.get("aws_iam_role"):
        return "AWS_IAM_ROLE"
    if cred.get("azure_managed_identity"):
        return "AZURE_MANAGED_IDENTITY"
    if cred.get("azure_service_principal"):
        return "AZURE_SERVICE_PRINCIPAL"
    if cred.get("databricks_gcp_service_account") or cred.get(
        "gcp_service_account_key"
    ):
        return "GCP_SERVICE_ACCOUNT"
    if cred.get("cloudflare_api_token"):
        return "CLOUDFLARE_API_TOKEN"
    return None


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: DatabricksWorkspaceClient,
    workspace_id: str,
    common_job_parameters: dict[str, Any],
) -> None:
    creds = get(api_session)
    transformed = transform(creds)
    load_storage_credentials(
        neo4j_session,
        transformed,
        workspace_id,
        common_job_parameters["UPDATE_TAG"],
    )


@timeit
def get(api_session: DatabricksWorkspaceClient) -> list[dict[str, Any]]:
    return api_session.uc_list(
        "/api/2.1/unity-catalog/storage-credentials", "storage_credentials"
    )


@timeit
def transform(creds: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for c in creds:
        name = c["name"]
        if not name:
            raise ValueError("Databricks storage credential returned with empty name")
        metastore_id = c["metastore_id"]
        aws = c.get("aws_iam_role") or {}
        azure_mi = c.get("azure_managed_identity") or {}
        gcp = c.get("databricks_gcp_service_account") or {}
        result.append(
            {
                # Names are only metastore-scoped, so a payload missing the API
                # id falls back to a metastore-scoped id (never a bare name that
                # could collide across metastores). uc_id fails loudly if the
                # metastore id is also missing.
                "id": c.get("id") or uc_id(metastore_id, name),
                "credential_id": c.get("id"),
                "name": name,
                "metastore_id": metastore_id,
                "credential_type": _credential_type(c),
                "owner": c.get("owner"),
                "read_only": c.get("read_only"),
                "used_for_managed_storage": c.get("used_for_managed_storage"),
                "isolation_mode": c.get("isolation_mode"),
                "comment": c.get("comment"),
                "aws_iam_role_arn": aws.get("role_arn"),
                "azure_managed_identity_id": azure_mi.get("managed_identity_id"),
                "azure_access_connector_id": azure_mi.get("access_connector_id"),
                "gcp_service_account_email": gcp.get("email"),
                "created_at": epoch_ms_to_datetime(c.get("created_at")),
                "updated_at": epoch_ms_to_datetime(c.get("updated_at")),
            }
        )
    return result


@timeit
def load_storage_credentials(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    workspace_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        DatabricksStorageCredentialSchema(),
        data,
        lastupdated=update_tag,
        WORKSPACE_ID=workspace_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(
        DatabricksStorageCredentialSchema(), common_job_parameters
    ).run(neo4j_session)
