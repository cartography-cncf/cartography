import os
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cartography.intel.common.object_store import BucketReader

_SOURCE_SCHEME_RE = re.compile(
    r"^(?P<scheme>[a-z][a-z0-9+.-]*)://(?P<rest>.*)$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class LocalReportSource:
    raw: str
    path: str

    @property
    def uri(self) -> str:
        return self.path


@dataclass(frozen=True)
class S3ReportSource:
    raw: str
    bucket: str
    prefix: str

    @property
    def uri(self) -> str:
        return build_s3_source(self.bucket, self.prefix)


@dataclass(frozen=True)
class GCSReportSource:
    raw: str
    bucket: str
    prefix: str

    @property
    def uri(self) -> str:
        return build_gcs_source(self.bucket, self.prefix)


@dataclass(frozen=True)
class AzureBlobReportSource:
    raw: str
    account_name: str
    container_name: str
    prefix: str

    @property
    def uri(self) -> str:
        return build_azblob_source(
            self.account_name,
            self.container_name,
            self.prefix,
        )


CloudReportSource = S3ReportSource | GCSReportSource | AzureBlobReportSource
ReportSource = LocalReportSource | CloudReportSource


def build_s3_source(bucket: str, prefix: str | None = None) -> str:
    normalized_prefix = (prefix or "").lstrip("/")
    if normalized_prefix:
        return f"s3://{bucket}/{normalized_prefix}"
    return f"s3://{bucket}"


def build_gcs_source(bucket: str, prefix: str | None = None) -> str:
    normalized_prefix = (prefix or "").lstrip("/")
    if normalized_prefix:
        return f"gs://{bucket}/{normalized_prefix}"
    return f"gs://{bucket}"


def build_azblob_source(
    account_name: str,
    container_name: str,
    prefix: str | None = None,
) -> str:
    normalized_prefix = (prefix or "").lstrip("/")
    if normalized_prefix:
        return f"azblob://{account_name}/{container_name}/{normalized_prefix}"
    return f"azblob://{account_name}/{container_name}"


def parse_report_source(raw_source: str) -> ReportSource:
    source = raw_source.strip()
    if not source:
        raise ValueError("Report source cannot be empty.")

    scheme_match = _SOURCE_SCHEME_RE.match(source)
    if not scheme_match:
        return LocalReportSource(raw=raw_source, path=os.path.expanduser(source))

    scheme = scheme_match.group("scheme").lower()
    remainder = scheme_match.group("rest")

    if scheme == "s3":
        bucket, _sep, prefix = remainder.partition("/")
        if not bucket:
            raise ValueError("S3 report source must include a bucket name.")
        return S3ReportSource(raw=raw_source, bucket=bucket, prefix=prefix)

    if scheme == "gs":
        bucket, _sep, prefix = remainder.partition("/")
        if not bucket:
            raise ValueError("GCS report source must include a bucket name.")
        return GCSReportSource(raw=raw_source, bucket=bucket, prefix=prefix)

    if scheme == "azblob":
        account_name, _sep, container_and_prefix = remainder.partition("/")
        container_name, _sep, prefix = container_and_prefix.partition("/")
        if not account_name or not container_name:
            raise ValueError(
                "Azure Blob report source must look like azblob://<account>/<container>/<prefix>.",
            )
        return AzureBlobReportSource(
            raw=raw_source,
            account_name=account_name,
            container_name=container_name,
            prefix=prefix,
        )

    raise ValueError(
        f"Unsupported report source scheme '{scheme}'. "
        "Supported schemes are s3://, gs://, and azblob://. "
        "Use a plain filesystem path for local sources.",
    )


def build_bucket_reader_for_source(
    source: CloudReportSource,
    *,
    azure_sp_auth: bool | None = None,
    azure_tenant_id: str | None = None,
    azure_client_id: str | None = None,
    azure_client_secret: str | None = None,
) -> tuple["BucketReader", str, str]:
    if isinstance(source, S3ReportSource):
        import boto3

        from cartography.intel.common.object_store import S3BucketReader

        return S3BucketReader(boto3.Session()), source.bucket, source.prefix

    if isinstance(source, GCSReportSource):
        from cartography.intel.common.object_store import GCSBucketReader

        return GCSBucketReader(), source.bucket, source.prefix

    from cartography.intel.common.object_store import AzureBlobContainerReader

    if azure_sp_auth:
        from cartography.intel.azure.util.credentials import Authenticator

        authenticator = Authenticator()
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
        from azure.identity import AzureCliCredential

        credential = AzureCliCredential()

    return (
        AzureBlobContainerReader(
            source.account_name,
            credential,
        ),
        source.container_name,
        source.prefix,
    )
