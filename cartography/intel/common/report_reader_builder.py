import logging

import cartography.intel.common.object_store as object_store
from cartography.intel.common.object_store import ReportReader
from cartography.intel.common.report_source import AzureBlobReportSource
from cartography.intel.common.report_source import GCSReportSource
from cartography.intel.common.report_source import LocalReportSource
from cartography.intel.common.report_source import ReportSource
from cartography.intel.common.report_source import S3ReportSource

logger = logging.getLogger(__name__)


def build_report_reader_for_source(
    source: ReportSource,
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
            source_uri=source.uri,
        )

    raise ValueError(f"Unsupported report source type: {type(source).__name__}")
