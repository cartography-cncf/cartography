from unittest.mock import MagicMock

import pytest

from cartography.intel.common.object_store import filter_object_refs
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
