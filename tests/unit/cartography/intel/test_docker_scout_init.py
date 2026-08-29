import logging
from unittest.mock import MagicMock
from unittest.mock import patch

from botocore.exceptions import ClientError

from cartography.intel.docker_scout import sync_docker_scout_from_dir
from cartography.intel.docker_scout import sync_docker_scout_from_s3


@patch("cartography.intel.docker_scout.cleanup")
@patch("cartography.intel.docker_scout.sync_from_file")
def test_sync_docker_scout_from_dir_skips_unicode_decode_errors(
    mock_sync_from_file,
    mock_cleanup,
    tmp_path,
    caplog,
) -> None:
    neo4j_session = MagicMock()
    report_path = tmp_path / "bad-report.txt"
    report_path.write_bytes(b"\x80")

    with caplog.at_level(logging.ERROR):
        sync_docker_scout_from_dir(
            neo4j_session,
            str(tmp_path),
            1,
            {"UPDATE_TAG": 1},
        )

    mock_sync_from_file.assert_not_called()
    mock_cleanup.assert_not_called()
    assert any(r.levelname == "ERROR" for r in caplog.records)


@patch("cartography.intel.docker_scout.cleanup")
@patch("cartography.intel.docker_scout.sync_from_file")
def test_sync_docker_scout_from_s3_skips_unicode_decode_errors(
    mock_sync_from_file,
    mock_cleanup,
    caplog,
) -> None:
    neo4j_session = MagicMock()
    boto3_session = MagicMock()
    s3_client = MagicMock()
    s3_client.get_paginator.return_value.paginate.return_value = [
        {"Contents": [{"Key": "reports/bad-report.txt"}]},
    ]
    s3_client.get_object.return_value = {
        "Body": MagicMock(read=MagicMock(return_value=b"\x80")),
    }
    boto3_session.client.return_value = s3_client

    with caplog.at_level(logging.ERROR):
        sync_docker_scout_from_s3(
            neo4j_session,
            "example-bucket",
            "reports/",
            1,
            {"UPDATE_TAG": 1},
            boto3_session,
        )

    mock_sync_from_file.assert_not_called()
    mock_cleanup.assert_not_called()
    assert any(r.levelname == "ERROR" for r in caplog.records)


@patch("cartography.intel.docker_scout.cleanup")
@patch("cartography.intel.docker_scout.sync_from_file")
def test_sync_docker_scout_from_s3_skips_read_failures(
    mock_sync_from_file,
    mock_cleanup,
    caplog,
) -> None:
    neo4j_session = MagicMock()
    boto3_session = MagicMock()
    s3_client = MagicMock()
    s3_client.get_paginator.return_value.paginate.return_value = [
        {"Contents": [{"Key": "reports/forbidden-report.txt"}]},
    ]
    s3_client.get_object.side_effect = ClientError(
        {"Error": {"Code": "AccessDenied", "Message": "access denied"}},
        "GetObject",
    )
    boto3_session.client.return_value = s3_client

    with caplog.at_level(logging.ERROR):
        sync_docker_scout_from_s3(
            neo4j_session,
            "example-bucket",
            "reports/",
            1,
            {"UPDATE_TAG": 1},
            boto3_session,
        )

    mock_sync_from_file.assert_not_called()
    mock_cleanup.assert_not_called()
    assert any(r.levelname == "ERROR" for r in caplog.records)
