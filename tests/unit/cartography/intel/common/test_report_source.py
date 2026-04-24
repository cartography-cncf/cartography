from unittest.mock import MagicMock

import pytest

from cartography.intel.common.report_source import AzureBlobReportSource
from cartography.intel.common.report_source import build_bucket_reader_for_source
from cartography.intel.common.report_source import GCSReportSource
from cartography.intel.common.report_source import LocalReportSource
from cartography.intel.common.report_source import parse_report_source
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


def test_build_bucket_reader_for_s3(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_session = object()
    fake_reader = object()

    monkeypatch.setattr("boto3.Session", lambda: fake_session)
    monkeypatch.setattr(
        "cartography.intel.common.object_store.S3BucketReader",
        lambda session: fake_reader,
    )

    reader, bucket_name, prefix = build_bucket_reader_for_source(
        S3ReportSource(raw="s3://bucket/prefix", bucket="bucket", prefix="prefix"),
    )

    assert reader is fake_reader
    assert bucket_name == "bucket"
    assert prefix == "prefix"


def test_build_bucket_reader_for_gcs(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_reader = object()
    monkeypatch.setattr(
        "cartography.intel.common.object_store.GCSBucketReader",
        lambda: fake_reader,
    )

    reader, bucket_name, prefix = build_bucket_reader_for_source(
        GCSReportSource(raw="gs://bucket/prefix", bucket="bucket", prefix="prefix"),
    )

    assert reader is fake_reader
    assert bucket_name == "bucket"
    assert prefix == "prefix"


def test_build_bucket_reader_for_azure_cli_auth(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_reader = object()
    fake_credential = object()

    def _build_reader(account_name, credential):
        assert account_name == "acct"
        assert credential is fake_credential
        return fake_reader

    monkeypatch.setattr(
        "azure.identity.AzureCliCredential",
        lambda: fake_credential,
    )
    monkeypatch.setattr(
        "cartography.intel.common.object_store.AzureBlobContainerReader",
        _build_reader,
    )

    reader, bucket_name, prefix = build_bucket_reader_for_source(
        AzureBlobReportSource(
            raw="azblob://acct/container/prefix",
            account_name="acct",
            container_name="container",
            prefix="prefix",
        ),
    )

    assert reader is fake_reader
    assert bucket_name == "container"
    assert prefix == "prefix"


def test_build_bucket_reader_for_azure_sp_auth(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_reader = object()
    fake_credentials = MagicMock(credential=object())
    fake_authenticator = MagicMock()
    fake_authenticator.authenticate_sp.return_value = fake_credentials

    monkeypatch.setattr(
        "cartography.intel.azure.util.credentials.Authenticator",
        lambda: fake_authenticator,
    )
    monkeypatch.setattr(
        "cartography.intel.common.object_store.AzureBlobContainerReader",
        lambda account_name, credential: fake_reader,
    )

    reader, bucket_name, prefix = build_bucket_reader_for_source(
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
    assert bucket_name == "container"
    assert prefix == "prefix"
    fake_authenticator.authenticate_sp.assert_called_once_with(
        tenant_id="tenant-id",
        client_id="client-id",
        client_secret="client-secret",
    )
