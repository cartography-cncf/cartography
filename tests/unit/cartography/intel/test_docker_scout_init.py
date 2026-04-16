from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

from cartography.intel.common.object_store import ObjectRef
from cartography.intel.docker_scout import sync_docker_scout_from_dir
from cartography.intel.docker_scout import sync_docker_scout_from_s3


def test_sync_docker_scout_from_dir_skips_unicode_decode_errors(
    tmp_path,
    caplog,
) -> None:
    neo4j_session = MagicMock()
    report_path = tmp_path / "bad-report.txt"
    report_path.write_bytes(b"\x80")

    with patch.object(
        Path,
        "read_text",
        side_effect=UnicodeDecodeError("utf-8", b"\x80", 0, 1, "invalid start byte"),
    ):
        sync_docker_scout_from_dir(
            neo4j_session,
            str(tmp_path),
            1,
            {"UPDATE_TAG": 1},
        )

    assert f"Skipping unreadable Docker Scout report {report_path}" in caplog.text


def test_sync_docker_scout_from_s3_skips_unicode_decode_errors(
    caplog,
) -> None:
    neo4j_session = MagicMock()
    boto3_session = MagicMock()
    s3_client = MagicMock()
    s3_client.get_object.return_value = {
        "Body": MagicMock(read=MagicMock(return_value=b"\x80")),
    }
    boto3_session.client.return_value = s3_client

    with patch(
        "cartography.intel.docker_scout.S3BucketReader.list_objects",
        return_value=[
            ObjectRef(
                "s3",
                "example-bucket",
                "reports/bad-report.txt",
            ),
        ],
    ):
        sync_docker_scout_from_s3(
            neo4j_session,
            "example-bucket",
            "reports/",
            1,
            {"UPDATE_TAG": 1},
            boto3_session,
        )

    assert (
        "Skipping unreadable Docker Scout report s3://example-bucket/reports/bad-report.txt"
        in caplog.text
    )
