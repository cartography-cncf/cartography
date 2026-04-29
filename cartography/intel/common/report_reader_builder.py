import logging
from typing import Any

import cartography.intel.common.object_store as object_store
from cartography.intel.common.object_store import ReportReader
from cartography.intel.common.report_source import AzureBlobReportSource
from cartography.intel.common.report_source import GCSReportSource
from cartography.intel.common.report_source import LocalReportSource
from cartography.intel.common.report_source import ReportSource
from cartography.intel.common.report_source import S3ReportSource

logger = logging.getLogger(__name__)


def _build_azure_credential(
    *,
    azure_sp_auth: bool | None,
    azure_tenant_id: str | None,
    azure_client_id: str | None,
    azure_client_secret: str | None,
) -> Any:
    # Blob data-plane access; we deliberately avoid the Azure resource-graph
    # Authenticator here because it requires subscription-list permission.
    from azure import identity as azure_identity

    if azure_sp_auth:
        if not (azure_tenant_id and azure_client_id and azure_client_secret):
            raise ValueError(
                "azure_sp_auth requires azure_tenant_id, azure_client_id, and azure_client_secret.",
            )
        return azure_identity.ClientSecretCredential(
            tenant_id=azure_tenant_id,
            client_id=azure_client_id,
            client_secret=azure_client_secret,
        )

    if azure_tenant_id or azure_client_id or azure_client_secret:
        logger.warning(
            "Azure service principal report-source settings were provided but azure_sp_auth is disabled; using Azure CLI credentials.",
        )
    return azure_identity.AzureCliCredential()


def build_report_reader_for_source(
    source: ReportSource,
    *,
    azure_sp_auth: bool | None = None,
    azure_tenant_id: str | None = None,
    azure_client_id: str | None = None,
    azure_client_secret: str | None = None,
) -> ReportReader:
    if isinstance(source, LocalReportSource):
        return object_store.LocalReportReader(source.path)

    if isinstance(source, S3ReportSource):
        import boto3

        return object_store.S3BucketReader(
            boto3.Session(),
            source.bucket,
            source.prefix,
            source.uri,
        )

    if isinstance(source, GCSReportSource):
        return object_store.GCSBucketReader(source.bucket, source.prefix, source.uri)

    if not isinstance(source, AzureBlobReportSource):
        raise ValueError(f"Unsupported report source type: {type(source).__name__}")

    credential = _build_azure_credential(
        azure_sp_auth=azure_sp_auth,
        azure_tenant_id=azure_tenant_id,
        azure_client_id=azure_client_id,
        azure_client_secret=azure_client_secret,
    )

    return object_store.AzureBlobContainerReader(
        source.account_name,
        source.container_name,
        source.prefix,
        credential,
        source.uri,
    )
