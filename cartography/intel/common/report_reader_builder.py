import importlib

import boto3
from azure import identity as azure_identity

import cartography.intel.common.object_store as object_store
from cartography.intel.common.object_store import ReportReader
from cartography.intel.common.report_source import GCSReportSource
from cartography.intel.common.report_source import LocalReportSource
from cartography.intel.common.report_source import ReportSource
from cartography.intel.common.report_source import S3ReportSource


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
        return object_store.S3BucketReader(
            boto3.Session(),
            source.bucket,
            source.prefix,
            source.uri,
        )

    if isinstance(source, GCSReportSource):
        return object_store.GCSBucketReader(source.bucket, source.prefix, source.uri)

    if azure_sp_auth:
        credentials_module = importlib.import_module(
            "cartography.intel.azure.util.credentials",
        )
        authenticator = credentials_module.Authenticator()
        credentials = authenticator.authenticate_sp(
            tenant_id=azure_tenant_id,
            client_id=azure_client_id,
            client_secret=azure_client_secret,
        )

        if credentials is None:
            raise RuntimeError(
                "Azure Blob report source was configured, but Azure credentials are not available.",
            )
        credential = credentials.credential
    else:
        credential = azure_identity.AzureCliCredential()

    return object_store.AzureBlobContainerReader(
        source.account_name,
        source.container_name,
        source.prefix,
        credential,
        source.uri,
    )
