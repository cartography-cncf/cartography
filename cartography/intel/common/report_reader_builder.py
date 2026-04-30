from typing import Any
from typing import TYPE_CHECKING

import cartography.intel.common.object_store as object_store
from cartography.intel.common.object_store import ReportReader
from cartography.intel.common.report_source import AzureBlobReportSource
from cartography.intel.common.report_source import GCSReportSource
from cartography.intel.common.report_source import LocalReportSource
from cartography.intel.common.report_source import ReportSource
from cartography.intel.common.report_source import S3ReportSource

if TYPE_CHECKING:
    from cartography.config import Config


def build_azure_blob_credential_from_config(config: "Config") -> Any | None:
    if not config.azure_sp_auth:
        return None

    if not (
        config.azure_tenant_id and config.azure_client_id and config.azure_client_secret
    ):
        raise ValueError(
            "azure_sp_auth requires azure_tenant_id, azure_client_id, and azure_client_secret.",
        )

    from azure.identity import ClientSecretCredential

    return ClientSecretCredential(
        tenant_id=config.azure_tenant_id,
        client_id=config.azure_client_id,
        client_secret=config.azure_client_secret,
    )


def build_report_reader_for_source(
    source: ReportSource,
    *,
    azure_blob_credential: Any | None = None,
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

    if isinstance(source, AzureBlobReportSource):
        return object_store.AzureBlobContainerReader(
            source.account_name,
            source.container_name,
            source.prefix,
            credential=azure_blob_credential,
            source_uri=source.uri,
        )

    raise ValueError(f"Unsupported report source type: {type(source).__name__}")
