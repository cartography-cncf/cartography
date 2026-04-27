import importlib
import logging
import os
import re
from dataclasses import dataclass

import boto3
from azure import identity as azure_identity

import cartography.intel.common.object_store as object_store
from cartography.intel.common.object_store import ReportReader

logger = logging.getLogger(__name__)

_DEPRECATED_REPORT_SOURCE_REMOVAL_VERSION = "v1.0.0"

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


@dataclass(frozen=True)
class LegacyReportSourceNames:
    """Display strings used in deprecation warnings and errors from
    `resolve_legacy_report_source`. The CLI passes flag names like
    `--trivy-source`; Config passes backtick-wrapped attribute names."""

    source: str
    local: str
    s3_bucket: str
    s3_prefix: str

    @classmethod
    def for_cli(cls, module: str) -> "LegacyReportSourceNames":
        base = f"--{module.replace('_', '-')}"
        return cls(
            source=f"{base}-source",
            local=f"{base}-results-dir",
            s3_bucket=f"{base}-s3-bucket",
            s3_prefix=f"{base}-s3-prefix",
        )

    @classmethod
    def for_config(cls, module: str) -> "LegacyReportSourceNames":
        return cls(
            source=f"`{module}_source`",
            local=f"`{module}_results_dir`",
            s3_bucket=f"`{module}_s3_bucket`",
            s3_prefix=f"`{module}_s3_prefix`",
        )


def resolve_legacy_report_source(
    *,
    source: str | None,
    local_path: str | None,
    s3_bucket: str | None,
    s3_prefix: str | None,
    names: LegacyReportSourceNames,
    warn_on_legacy: bool = True,
) -> str | None:
    if source is not None and (local_path or s3_bucket or s3_prefix):
        raise ValueError(
            f"Cannot use {names.source} with deprecated source flags "
            f"({names.local}, {names.s3_bucket}, {names.s3_prefix}).",
        )
    if local_path and (s3_bucket or s3_prefix):
        raise ValueError(
            f"Cannot use both {names.local} and {names.s3_bucket}/{names.s3_prefix}. "
            f"Use {names.source} instead.",
        )
    if s3_prefix and not s3_bucket:
        raise ValueError(f"{names.s3_prefix} requires {names.s3_bucket}.")

    if source is not None:
        parse_report_source(source)
        return source

    if local_path:
        if warn_on_legacy:
            logger.warning(
                "DEPRECATED: %s will be removed in Cartography %s; use %s instead.",
                names.local,
                _DEPRECATED_REPORT_SOURCE_REMOVAL_VERSION,
                names.source,
            )
        parse_report_source(local_path)
        return local_path

    if s3_bucket:
        if warn_on_legacy:
            logger.warning(
                "DEPRECATED: %s/%s will be removed in Cartography %s; use %s instead.",
                names.s3_bucket,
                names.s3_prefix,
                _DEPRECATED_REPORT_SOURCE_REMOVAL_VERSION,
                names.source,
            )
        resolved_source = build_s3_source(s3_bucket, s3_prefix)
        parse_report_source(resolved_source)
        return resolved_source

    return None
