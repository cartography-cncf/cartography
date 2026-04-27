from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from cartography.intel.common.report_reader_builder import (
    build_report_reader_for_source,
)
from cartography.intel.common.report_source import AzureBlobReportSource
from cartography.intel.common.report_source import GCSReportSource
from cartography.intel.common.report_source import LegacyReportSourceNames
from cartography.intel.common.report_source import LocalReportSource
from cartography.intel.common.report_source import parse_report_source
from cartography.intel.common.report_source import (
    resolve_report_source_with_legacy_fields,
)
from cartography.intel.common.report_source import S3ReportSource


def test_parse_local_report_source_from_plain_path() -> None:
    source = parse_report_source("./reports/trivy")

    assert source == LocalReportSource(raw="./reports/trivy", path="./reports/trivy")


def test_parse_local_report_source_from_windows_path() -> None:
    source = parse_report_source(r"C:\reports\syft")

    assert source == LocalReportSource(
        raw=r"C:\reports\syft",
        path=r"C:\reports\syft",
    )


def test_parse_s3_report_source() -> None:
    source = parse_report_source("s3://example-bucket/reports/trivy/")

    assert source == S3ReportSource(
        raw="s3://example-bucket/reports/trivy/",
        bucket="example-bucket",
        prefix="reports/trivy/",
    )


def test_parse_report_source_accepts_uppercase_scheme() -> None:
    source = parse_report_source("S3://example-bucket/reports/trivy/")

    assert source == S3ReportSource(
        raw="S3://example-bucket/reports/trivy/",
        bucket="example-bucket",
        prefix="reports/trivy/",
    )


def test_parse_gcs_report_source() -> None:
    source = parse_report_source("gs://example-bucket/reports/syft")

    assert source == GCSReportSource(
        raw="gs://example-bucket/reports/syft",
        bucket="example-bucket",
        prefix="reports/syft",
    )


def test_parse_azblob_report_source() -> None:
    source = parse_report_source("azblob://acct/container/reports/aibom")

    assert source == AzureBlobReportSource(
        raw="azblob://acct/container/reports/aibom",
        account_name="acct",
        container_name="container",
        prefix="reports/aibom",
    )


def test_parse_report_source_rejects_unknown_scheme() -> None:
    with pytest.raises(ValueError, match="Unsupported report source scheme"):
        parse_report_source("ftp://example.com/reports")


def test_resolve_report_source_with_legacy_fields_rejects_explicit_empty_source() -> (
    None
):
    with pytest.raises(ValueError, match="Report source cannot be empty"):
        resolve_report_source_with_legacy_fields(
            source="",
            local_path=None,
            s3_bucket=None,
            s3_prefix=None,
            names=LegacyReportSourceNames.for_cli("trivy"),
        )


def test_resolve_report_source_with_legacy_fields_rejects_explicit_empty_source_with_legacy() -> (
    None
):
    with pytest.raises(ValueError, match="Cannot use --trivy-source"):
        resolve_report_source_with_legacy_fields(
            source="",
            local_path="/tmp/results",
            s3_bucket=None,
            s3_prefix=None,
            names=LegacyReportSourceNames.for_cli("trivy"),
        )


def test_resolve_report_source_with_legacy_fields_treats_none_source_as_unset() -> None:
    assert (
        resolve_report_source_with_legacy_fields(
            source=None,
            local_path=None,
            s3_bucket=None,
            s3_prefix=None,
            names=LegacyReportSourceNames.for_cli("trivy"),
        )
        is None
    )


def test_resolve_report_source_with_legacy_fields_rejects_explicit_empty_local_path() -> (
    None
):
    with pytest.raises(ValueError, match="Report source cannot be empty"):
        resolve_report_source_with_legacy_fields(
            source=None,
            local_path="",
            s3_bucket=None,
            s3_prefix=None,
            names=LegacyReportSourceNames.for_cli("trivy"),
        )


@patch("cartography.intel.common.object_store.LocalReportReader")
def test_build_report_reader_for_local(mock_reader_cls) -> None:
    fake_reader = mock_reader_cls.return_value

    reader = build_report_reader_for_source(
        LocalReportSource(raw="./reports", path="./reports"),
    )

    assert reader is fake_reader
    mock_reader_cls.assert_called_once_with("./reports")


@patch("cartography.intel.common.object_store.S3BucketReader")
@patch("boto3.Session")
def test_build_report_reader_for_s3(
    mock_session_cls,
    mock_reader_cls,
) -> None:
    fake_session = mock_session_cls.return_value
    fake_reader = mock_reader_cls.return_value

    reader = build_report_reader_for_source(
        S3ReportSource(raw="s3://bucket/prefix", bucket="bucket", prefix="prefix"),
    )

    assert reader is fake_reader
    mock_reader_cls.assert_called_once_with(
        fake_session,
        "bucket",
        "prefix",
        "s3://bucket/prefix",
    )


@patch("cartography.intel.common.object_store.GCSBucketReader")
def test_build_report_reader_for_gcs(mock_reader_cls) -> None:
    fake_reader = mock_reader_cls.return_value

    reader = build_report_reader_for_source(
        GCSReportSource(raw="gs://bucket/prefix", bucket="bucket", prefix="prefix"),
    )

    assert reader is fake_reader
    mock_reader_cls.assert_called_once_with("bucket", "prefix", "gs://bucket/prefix")


def test_build_report_reader_for_source_rejects_unknown_source_type() -> None:
    with pytest.raises(ValueError, match="Unsupported report source type"):
        build_report_reader_for_source(object())  # type: ignore[arg-type]


@patch("cartography.intel.common.object_store.AzureBlobContainerReader")
@patch("azure.identity.AzureCliCredential")
def test_build_report_reader_for_azure_cli_auth(
    mock_credential_cls,
    mock_reader_cls,
) -> None:
    fake_reader = mock_reader_cls.return_value
    fake_credential = mock_credential_cls.return_value

    reader = build_report_reader_for_source(
        AzureBlobReportSource(
            raw="azblob://acct/container/prefix",
            account_name="acct",
            container_name="container",
            prefix="prefix",
        ),
    )

    assert reader is fake_reader
    mock_reader_cls.assert_called_once_with(
        "acct",
        "container",
        "prefix",
        fake_credential,
        "azblob://acct/container/prefix",
    )


@patch("cartography.intel.common.object_store.AzureBlobContainerReader")
@patch("cartography.intel.azure.util.credentials.Authenticator")
def test_build_report_reader_for_azure_sp_auth(
    mock_authenticator_cls,
    mock_reader_cls,
) -> None:
    fake_reader = mock_reader_cls.return_value
    fake_credentials = MagicMock(credential=object())
    fake_authenticator = mock_authenticator_cls.return_value
    fake_authenticator.authenticate_sp.return_value = fake_credentials

    reader = build_report_reader_for_source(
        AzureBlobReportSource(
            raw="azblob://acct/container/prefix",
            account_name="acct",
            container_name="container",
            prefix="prefix",
        ),
        azure_sp_auth=True,
        azure_tenant_id="tenant-id",
        azure_client_id="client-id",
        azure_client_secret="client-secret",
    )

    assert reader is fake_reader
    fake_authenticator.authenticate_sp.assert_called_once_with(
        tenant_id="tenant-id",
        client_id="client-id",
        client_secret="client-secret",
    )
    mock_reader_cls.assert_called_once_with(
        "acct",
        "container",
        "prefix",
        fake_credentials.credential,
        "azblob://acct/container/prefix",
    )
