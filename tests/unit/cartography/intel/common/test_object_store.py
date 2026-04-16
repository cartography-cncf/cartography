from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from cartography.intel.common.object_store import AzureBlobContainerReader
from cartography.intel.common.object_store import filter_object_refs
from cartography.intel.common.object_store import GCSBucketReader
from cartography.intel.common.object_store import ObjectRef
from cartography.intel.common.object_store import ObjectStoreParseError
from cartography.intel.common.object_store import read_json_document
from cartography.intel.common.object_store import read_text_document
from cartography.intel.common.object_store import S3BucketReader


def test_object_ref_uri() -> None:
    ref = ObjectRef(provider="s3", bucket="example-bucket", key="reports/findings.json")
    assert ref.uri == "s3://example-bucket/reports/findings.json"


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

    refs = S3BucketReader(session).list_objects("example-bucket", "reports/")

    assert refs == [
        ObjectRef("s3", "example-bucket", "reports/findings-1.json"),
        ObjectRef("s3", "example-bucket", "reports/findings-2.txt"),
        ObjectRef("s3", "example-bucket", "reports/findings-3.json"),
    ]
    assert session.client.call_count == 1
    assert session.client.call_args.args[0] == "s3"
    session.client.return_value.get_paginator.assert_called_once_with("list_objects_v2")


def test_filter_object_refs_by_suffix() -> None:
    refs = [
        ObjectRef("s3", "example-bucket", "reports/a.json"),
        ObjectRef("s3", "example-bucket", "reports/a.txt"),
    ]

    assert filter_object_refs(refs, suffix=".json") == [refs[0]]


def test_s3_bucket_reader_reads_bytes() -> None:
    session = MagicMock()
    session.client.return_value.get_object.return_value = {
        "Body": MagicMock(read=MagicMock(return_value=b"hello")),
    }

    data = S3BucketReader(session).read_bytes(
        ObjectRef("s3", "example-bucket", "reports/findings.txt"),
    )

    assert data == b"hello"
    session.client.return_value.get_object.assert_called_once_with(
        Bucket="example-bucket",
        Key="reports/findings.txt",
    )


def test_gcs_bucket_reader_lists_objects_and_reads_bytes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_client = MagicMock()
    fake_client.list_blobs.return_value = [
        SimpleNamespace(name="reports/"),
        SimpleNamespace(name="reports/findings.json"),
    ]
    fake_bucket = fake_client.bucket.return_value
    fake_bucket.blob.return_value.download_as_bytes.return_value = b"hello"

    monkeypatch.setattr(
        "cartography.intel.gcp.clients.get_gcp_credentials",
        lambda: object(),
    )
    monkeypatch.setattr(
        "google.cloud.storage.Client",
        lambda credentials=None: fake_client,
    )

    reader = GCSBucketReader()
    refs = reader.list_objects("example-bucket", "reports/")

    assert refs == [ObjectRef("gs", "example-bucket", "reports/findings.json")]
    assert (
        reader.read_bytes(
            ObjectRef("gs", "example-bucket", "reports/findings.json"),
        )
        == b"hello"
    )


def test_azure_blob_reader_lists_objects_and_reads_bytes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_service_client = MagicMock()
    fake_service_client.get_container_client.return_value.list_blobs.return_value = [
        SimpleNamespace(name="reports/"),
        SimpleNamespace(name="reports/findings.txt"),
    ]
    fake_service_client.get_blob_client.return_value.download_blob.return_value.readall.return_value = (
        b"hello"
    )

    monkeypatch.setattr(
        "azure.storage.blob.BlobServiceClient",
        lambda account_url, credential: fake_service_client,
    )

    reader = AzureBlobContainerReader("acct", object())
    refs = reader.list_objects("container", "reports/")

    assert refs == [ObjectRef("azblob", "acct/container", "reports/findings.txt")]
    assert (
        reader.read_bytes(
            ObjectRef("azblob", "acct/container", "reports/findings.txt"),
        )
        == b"hello"
    )


def test_read_text_document_reports_source_on_decode_error() -> None:
    reader = MagicMock()
    ref = ObjectRef("s3", "example-bucket", "reports/bad.txt")
    reader.read_bytes.return_value = b"\x80"

    with pytest.raises(ObjectStoreParseError, match=ref.uri):
        read_text_document(reader, ref)


def test_read_json_document_reports_source_on_parse_error() -> None:
    reader = MagicMock()
    ref = ObjectRef("s3", "example-bucket", "reports/bad.json")
    reader.read_bytes.return_value = b"{not-json"

    with pytest.raises(ObjectStoreParseError, match=ref.uri):
        read_json_document(reader, ref)
