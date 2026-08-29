from types import SimpleNamespace
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from cartography.intel.common.object_store import AzureBlobContainerReader
from cartography.intel.common.object_store import filter_report_refs
from cartography.intel.common.object_store import GCSBucketReader
from cartography.intel.common.object_store import LocalReportReader
from cartography.intel.common.object_store import ObjectStoreError
from cartography.intel.common.object_store import read_json_report
from cartography.intel.common.object_store import read_text_report
from cartography.intel.common.object_store import ReportRef
from cartography.intel.common.object_store import S3BucketReader


def test_local_report_reader_lists_files_and_reads_bytes(tmp_path) -> None:
    reports = tmp_path / "reports"
    nested = reports / "nested"
    nested.mkdir(parents=True)
    report = nested / "findings.json"
    report.write_bytes(b"hello")
    hidden = reports / ".hidden.json"
    hidden.write_bytes(b"hidden")

    reader = LocalReportReader(str(reports))
    refs = sorted(reader.list_reports(), key=lambda ref: ref.name)

    assert refs == [
        ReportRef(uri=str(hidden), name=".hidden.json"),
        ReportRef(uri=str(report), name="nested/findings.json"),
    ]
    assert reader.source_uri == str(reports)
    assert reader.read_bytes(refs[1]) == b"hello"


def test_local_report_reader_accepts_single_file(tmp_path) -> None:
    report = tmp_path / "findings.json"
    report.write_bytes(b"hello")

    reader = LocalReportReader(str(report))
    refs = reader.list_reports()

    assert refs == [
        ReportRef(uri=str(report), name="findings.json"),
    ]
    assert reader.read_bytes(refs[0]) == b"hello"


def test_local_report_reader_wraps_read_errors(tmp_path) -> None:
    reports = tmp_path / "reports"
    reports.mkdir()
    ref = ReportRef(uri=str(reports / "deleted.json"), name="deleted.json")

    with pytest.raises(ObjectStoreError, match=ref.uri):
        LocalReportReader(str(reports)).read_bytes(ref)


def test_s3_bucket_reader_lists_objects_and_skips_pseudo_directories() -> None:
    session = MagicMock()
    session.client.return_value.get_paginator.return_value.paginate.return_value = [
        {
            "Contents": [
                {"Key": "reports/"},
                {"Key": "reports/findings-1.json"},
                {"Key": "reports/findings-2.txt"},
            ],
        },
        {
            "Contents": [
                {"Key": "reports/findings-3.json"},
            ],
        },
    ]

    reader = S3BucketReader(session, "example-bucket", "reports/")
    refs = reader.list_reports()

    assert refs == [
        ReportRef(
            "s3://example-bucket/reports/findings-1.json", "reports/findings-1.json"
        ),
        ReportRef(
            "s3://example-bucket/reports/findings-2.txt", "reports/findings-2.txt"
        ),
        ReportRef(
            "s3://example-bucket/reports/findings-3.json", "reports/findings-3.json"
        ),
    ]
    assert reader.source_uri == "s3://example-bucket/reports/"
    assert session.client.call_count == 1
    assert session.client.call_args.args[0] == "s3"
    session.client.return_value.get_paginator.assert_called_once_with("list_objects_v2")


def test_filter_report_refs_by_suffix() -> None:
    refs = [
        ReportRef("s3://example-bucket/reports/a.json", "reports/a.json"),
        ReportRef("s3://example-bucket/reports/a.txt", "reports/a.txt"),
    ]

    assert filter_report_refs(refs, suffix=".json") == [refs[0]]


def test_s3_bucket_reader_reads_bytes() -> None:
    session = MagicMock()
    session.client.return_value.get_object.return_value = {
        "Body": MagicMock(read=MagicMock(return_value=b"hello")),
    }

    data = S3BucketReader(session, "example-bucket", "reports/").read_bytes(
        ReportRef("s3://example-bucket/reports/findings.txt", "reports/findings.txt"),
    )

    assert data == b"hello"
    session.client.return_value.get_object.assert_called_once_with(
        Bucket="example-bucket",
        Key="reports/findings.txt",
    )


def test_s3_bucket_reader_wraps_read_errors() -> None:
    from botocore.exceptions import ClientError

    session = MagicMock()
    session.client.return_value.get_object.side_effect = ClientError(
        {"Error": {"Code": "NoSuchKey", "Message": "not found"}},
        "GetObject",
    )
    ref = ReportRef("s3://example-bucket/reports/findings.txt", "reports/findings.txt")

    with pytest.raises(ObjectStoreError, match=ref.uri):
        S3BucketReader(session, "example-bucket", "reports/").read_bytes(ref)


@patch("google.cloud.storage.Client")
@patch("cartography.intel.gcp.clients.get_gcp_credentials")
def test_gcs_bucket_reader_lists_objects_and_reads_bytes(
    mock_get_gcp_credentials,
    mock_storage_client_cls,
) -> None:
    fake_client = MagicMock()
    fake_client.list_blobs.return_value = [
        SimpleNamespace(name="reports/"),
        SimpleNamespace(name="reports/findings.json"),
    ]
    fake_bucket = fake_client.bucket.return_value
    fake_bucket.blob.return_value.download_as_bytes.return_value = b"hello"
    fake_credentials = object()
    mock_get_gcp_credentials.return_value = fake_credentials
    mock_storage_client_cls.return_value = fake_client

    reader = GCSBucketReader("example-bucket", "reports/")
    refs = reader.list_reports()

    assert refs == [
        ReportRef("gs://example-bucket/reports/findings.json", "reports/findings.json")
    ]
    assert (
        reader.read_bytes(
            ReportRef(
                "gs://example-bucket/reports/findings.json", "reports/findings.json"
            ),
        )
        == b"hello"
    )
    mock_storage_client_cls.assert_called_once_with(credentials=fake_credentials)


@patch("google.cloud.storage.Client")
@patch("cartography.intel.gcp.clients.get_gcp_credentials")
def test_gcs_bucket_reader_wraps_read_errors(
    _mock_get_gcp_credentials,
    mock_storage_client_cls,
) -> None:
    from google.api_core import exceptions as google_exceptions

    fake_client = MagicMock()
    fake_client.bucket.return_value.blob.return_value.download_as_bytes.side_effect = (
        google_exceptions.NotFound("not found")
    )
    mock_storage_client_cls.return_value = fake_client
    ref = ReportRef("gs://example-bucket/reports/findings.txt", "reports/findings.txt")

    with pytest.raises(ObjectStoreError, match=ref.uri):
        GCSBucketReader("example-bucket", "reports/").read_bytes(ref)


@patch("azure.storage.blob.BlobServiceClient")
def test_azure_blob_reader_lists_objects_and_reads_bytes(
    mock_blob_service_client_cls,
) -> None:
    fake_service_client = MagicMock()
    fake_service_client.get_container_client.return_value.list_blobs.return_value = [
        SimpleNamespace(name="reports/"),
        SimpleNamespace(name="reports/findings.txt"),
    ]
    fake_service_client.get_blob_client.return_value.download_blob.return_value.readall.return_value = (
        b"hello"
    )
    mock_blob_service_client_cls.return_value = fake_service_client

    reader = AzureBlobContainerReader("acct", "container", "reports/", object())
    refs = reader.list_reports()

    assert refs == [
        ReportRef(
            "azblob://acct/container/reports/findings.txt",
            "reports/findings.txt",
        ),
    ]
    assert (
        reader.read_bytes(
            ReportRef(
                "azblob://acct/container/reports/findings.txt",
                "reports/findings.txt",
            ),
        )
        == b"hello"
    )


@patch("azure.identity.AzureCliCredential")
@patch("azure.storage.blob.BlobServiceClient")
def test_azure_blob_reader_creates_cli_credential_when_none_supplied(
    mock_blob_service_client_cls,
    mock_credential_cls,
) -> None:
    fake_credential = mock_credential_cls.return_value

    AzureBlobContainerReader("acct", "container", "reports/", credential=None)

    mock_credential_cls.assert_called_once_with()
    mock_blob_service_client_cls.assert_called_once_with(
        account_url="https://acct.blob.core.windows.net",
        credential=fake_credential,
    )


@patch("azure.identity.AzureCliCredential")
@patch("azure.storage.blob.BlobServiceClient")
def test_azure_blob_reader_uses_supplied_credential(
    mock_blob_service_client_cls,
    mock_credential_cls,
) -> None:
    fake_credential = object()

    AzureBlobContainerReader("acct", "container", "reports/", fake_credential)

    mock_credential_cls.assert_not_called()
    mock_blob_service_client_cls.assert_called_once_with(
        account_url="https://acct.blob.core.windows.net",
        credential=fake_credential,
    )


@patch("azure.storage.blob.BlobServiceClient")
def test_azure_blob_reader_wraps_read_errors(
    mock_blob_service_client_cls,
) -> None:
    from azure.core import exceptions as azure_exceptions

    fake_service_client = MagicMock()
    fake_service_client.get_blob_client.return_value.download_blob.return_value.readall.side_effect = azure_exceptions.ResourceNotFoundError(
        "not found"
    )
    mock_blob_service_client_cls.return_value = fake_service_client
    ref = ReportRef(
        "azblob://acct/container/reports/findings.txt",
        "reports/findings.txt",
    )

    with pytest.raises(ObjectStoreError, match=ref.uri):
        AzureBlobContainerReader("acct", "container", "reports/", object()).read_bytes(
            ref,
        )


def test_read_text_report_reports_source_on_decode_error() -> None:
    reader = MagicMock()
    ref = ReportRef("s3://example-bucket/reports/bad.txt", "reports/bad.txt")
    reader.read_bytes.return_value = b"\x80"

    with pytest.raises(ObjectStoreError, match=ref.uri):
        read_text_report(reader, ref)


def test_read_json_report_reports_source_on_parse_error() -> None:
    reader = MagicMock()
    ref = ReportRef("s3://example-bucket/reports/bad.json", "reports/bad.json")
    reader.read_bytes.return_value = b"{not-json"

    with pytest.raises(ObjectStoreError, match=ref.uri):
        read_json_report(reader, ref)
