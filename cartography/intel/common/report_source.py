import logging
import os
import re
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# RFC 3986 scheme grammar: ALPHA *( ALPHA / DIGIT / "+" / "-" / "." )
_SOURCE_SCHEME_RE = re.compile(
    r"^(?P<scheme>[a-z][a-z0-9+.-]*)://(?P<rest>.*)$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class LocalReportSource:
    """A filesystem path to a single report or a directory of reports."""

    path: str

    @property
    def uri(self) -> str:
        return self.path


@dataclass(frozen=True)
class S3ReportSource:
    """An S3 bucket+prefix. `prefix` never has a leading slash."""

    bucket: str
    prefix: str

    @property
    def uri(self) -> str:
        return build_s3_source(self.bucket, self.prefix)


@dataclass(frozen=True)
class GCSReportSource:
    """A GCS bucket+prefix. `prefix` never has a leading slash."""

    bucket: str
    prefix: str

    @property
    def uri(self) -> str:
        return build_gcs_source(self.bucket, self.prefix)


@dataclass(frozen=True)
class AzureBlobReportSource:
    """An Azure Blob Storage container+prefix. `prefix` never has a leading slash."""

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


def _normalize_cloud_prefix(provider: str, prefix: str | None = None) -> str:
    raw_prefix = prefix or ""
    normalized_prefix = raw_prefix.lstrip("/")
    if raw_prefix != normalized_prefix:
        logger.debug(
            "%s report source prefix %r had leading slashes removed.",
            provider,
            raw_prefix,
        )
    return normalized_prefix


def build_s3_source(bucket: str, prefix: str | None = None) -> str:
    normalized_prefix = _normalize_cloud_prefix("S3", prefix)
    if normalized_prefix:
        return f"s3://{bucket}/{normalized_prefix}"
    return f"s3://{bucket}"


def build_gcs_source(bucket: str, prefix: str | None = None) -> str:
    normalized_prefix = _normalize_cloud_prefix("GCS", prefix)
    if normalized_prefix:
        return f"gs://{bucket}/{normalized_prefix}"
    return f"gs://{bucket}"


def build_azblob_source(
    account_name: str,
    container_name: str,
    prefix: str | None = None,
) -> str:
    normalized_prefix = _normalize_cloud_prefix("Azure Blob", prefix)
    if normalized_prefix:
        return f"azblob://{account_name}/{container_name}/{normalized_prefix}"
    return f"azblob://{account_name}/{container_name}"


def parse_report_source(raw_source: str) -> ReportSource:
    source = raw_source.strip()
    if not source:
        raise ValueError("Report source cannot be empty.")

    scheme_match = _SOURCE_SCHEME_RE.match(source)
    if not scheme_match:
        return LocalReportSource(path=os.path.expanduser(source))

    scheme = scheme_match.group("scheme").lower()
    remainder = scheme_match.group("rest")

    if scheme == "s3":
        bucket, _sep, prefix = remainder.partition("/")
        if not bucket:
            raise ValueError("S3 report source must include a bucket name.")
        return S3ReportSource(
            bucket=bucket,
            prefix=_normalize_cloud_prefix("S3", prefix),
        )

    if scheme == "gs":
        bucket, _sep, prefix = remainder.partition("/")
        if not bucket:
            raise ValueError("GCS report source must include a bucket name.")
        return GCSReportSource(
            bucket=bucket,
            prefix=_normalize_cloud_prefix("GCS", prefix),
        )

    if scheme == "azblob":
        account_name, _sep, container_and_prefix = remainder.partition("/")
        container_name, _sep, prefix = container_and_prefix.partition("/")
        if not account_name or not container_name:
            raise ValueError(
                "Azure Blob report source must look like azblob://<account>/<container>/<prefix>.",
            )
        return AzureBlobReportSource(
            account_name=account_name,
            container_name=container_name,
            prefix=_normalize_cloud_prefix("Azure Blob", prefix),
        )

    raise ValueError(
        f"Unsupported report source scheme '{scheme}'. "
        "Supported schemes are s3://, gs://, and azblob://. "
        "Use a plain filesystem path for local sources.",
    )


@dataclass(frozen=True)
class LegacyReportSourceNames:
    """Display strings used in deprecation warnings and errors from
    `resolve_report_source_with_legacy_fields`. The CLI passes flag names like
    `--trivy-source`; Config passes backtick-wrapped attribute names."""

    source: str
    local: str
    s3_bucket: str
    s3_prefix: str

    @classmethod
    def for_cli(cls, module: str) -> "LegacyReportSourceNames":
        # CLI flags use dashes even when Config fields use underscores.
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


def resolve_report_source_with_legacy_fields(
    *,
    source: str | None,
    local_path: str | None,
    s3_bucket: str | None,
    s3_prefix: str | None,
    names: LegacyReportSourceNames,
    warn_on_legacy: bool = True,
) -> str | None:
    if source is not None and (
        local_path is not None or s3_bucket is not None or s3_prefix is not None
    ):
        raise ValueError(
            f"Cannot use {names.source} with deprecated source flags "
            f"({names.local}, {names.s3_bucket}, {names.s3_prefix}).",
        )
    if local_path is not None and (s3_bucket is not None or s3_prefix is not None):
        raise ValueError(
            f"Cannot use both {names.local} and {names.s3_bucket}/{names.s3_prefix}. "
            f"Use {names.source} instead.",
        )
    if s3_prefix is not None and s3_bucket is None:
        raise ValueError(f"{names.s3_prefix} requires {names.s3_bucket}.")

    if source is not None:
        parse_report_source(source)
        return source

    if local_path is not None:
        if warn_on_legacy:
            logger.warning(
                "DEPRECATED: %s will be removed in Cartography %s; use %s instead.",
                names.local,
                "v1.0.0",
                names.source,
            )
        parse_report_source(local_path)
        return local_path

    if s3_bucket is not None:
        if warn_on_legacy:
            logger.warning(
                "DEPRECATED: %s/%s will be removed in Cartography %s; use %s instead.",
                names.s3_bucket,
                names.s3_prefix,
                "v1.0.0",
                names.source,
            )
        resolved_source = build_s3_source(s3_bucket, s3_prefix)
        parse_report_source(resolved_source)
        return resolved_source

    return None
