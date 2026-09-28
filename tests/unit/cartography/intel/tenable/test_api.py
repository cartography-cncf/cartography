from unittest.mock import MagicMock

import pytest
import requests

from cartography.intel.tenable import api

TEST_BASE_URL = "https://cloud.tenable.com"
TEST_EXPORT_PATH = "assets/v2/export"
TEST_RESULT_BASE = "assets/export"
TEST_EXPORT_PARAMS = {"chunk_size": 1000}


def test_export_and_download_aggregates_finished_chunks(mocker):
    # Arrange
    session = MagicMock()
    mocker.patch.object(api, "_initiate_export", return_value="export-uuid")
    mocker.patch.object(
        api,
        "_get_export_status",
        return_value={"status": "FINISHED", "chunks_available": [2, 1]},
    )
    mock_download = mocker.patch.object(
        api,
        "_download_chunk",
        side_effect=[[{"id": "asset-2"}], [{"id": "asset-1"}]],
    )

    # Act
    result = api.export_and_download(
        session,
        TEST_BASE_URL,
        TEST_EXPORT_PATH,
        TEST_RESULT_BASE,
        TEST_EXPORT_PARAMS,
    )

    # Assert
    assert result == [{"id": "asset-2"}, {"id": "asset-1"}]
    assert [call.args[-1] for call in mock_download.call_args_list] == [2, 1]


def test_export_and_download_accepts_finished_export_without_chunks(mocker):
    # Arrange
    session = MagicMock()
    mocker.patch.object(api, "_initiate_export", return_value="export-uuid")
    mocker.patch.object(
        api,
        "_get_export_status",
        return_value={"status": "FINISHED", "chunks_available": []},
    )
    mock_download = mocker.patch.object(api, "_download_chunk")

    # Act
    result = api.export_and_download(
        session,
        TEST_BASE_URL,
        TEST_EXPORT_PATH,
        TEST_RESULT_BASE,
        TEST_EXPORT_PARAMS,
    )

    # Assert
    assert result == []
    mock_download.assert_not_called()


@pytest.mark.parametrize(
    ("status", "message"),
    [
        ("ERROR", "failed with status ERROR"),
        ("CANCELLED", "was cancelled"),
    ],
)
def test_export_and_download_rejects_terminal_failure_statuses(
    mocker,
    status,
    message,
):
    # Arrange
    mocker.patch.object(api, "_initiate_export", return_value="export-uuid")
    mocker.patch.object(api, "_get_export_status", return_value={"status": status})

    # Act and assert
    with pytest.raises(RuntimeError, match=message):
        api.export_and_download(
            MagicMock(),
            TEST_BASE_URL,
            TEST_EXPORT_PATH,
            TEST_RESULT_BASE,
            TEST_EXPORT_PARAMS,
        )


@pytest.mark.parametrize(
    "status_data",
    [
        {},
        {"status": "FINISHED"},
    ],
)
def test_export_and_download_rejects_malformed_status_payloads(
    mocker,
    status_data,
):
    # Arrange
    mocker.patch.object(api, "_initiate_export", return_value="export-uuid")
    mocker.patch.object(api, "_get_export_status", return_value=status_data)

    # Act and assert
    with pytest.raises(KeyError):
        api.export_and_download(
            MagicMock(),
            TEST_BASE_URL,
            TEST_EXPORT_PATH,
            TEST_RESULT_BASE,
            TEST_EXPORT_PARAMS,
        )


@pytest.mark.parametrize("chunks_available", [{}, "", None])
def test_export_and_download_rejects_non_list_chunks_available(
    mocker,
    chunks_available,
):
    # Arrange
    mocker.patch.object(api, "_initiate_export", return_value="export-uuid")
    mocker.patch.object(
        api,
        "_get_export_status",
        return_value={
            "status": "FINISHED",
            "chunks_available": chunks_available,
        },
    )

    # Act and assert
    with pytest.raises(TypeError, match="chunks_available returned"):
        api.export_and_download(
            MagicMock(),
            TEST_BASE_URL,
            TEST_EXPORT_PATH,
            TEST_RESULT_BASE,
            TEST_EXPORT_PARAMS,
        )


@pytest.mark.parametrize(
    ("field_name", "chunk_ids"),
    [
        ("chunks_failed", [2]),
        ("chunks_cancelled", [3, 4]),
    ],
)
def test_export_and_download_rejects_incomplete_finished_export(
    mocker,
    field_name,
    chunk_ids,
):
    # Arrange
    mocker.patch.object(api, "_initiate_export", return_value="export-uuid")
    mocker.patch.object(
        api,
        "_get_export_status",
        return_value={
            "status": "FINISHED",
            "chunks_available": [1],
            field_name: chunk_ids,
        },
    )
    mock_download = mocker.patch.object(api, "_download_chunk")

    # Act and assert
    with pytest.raises(RuntimeError, match="finished with incomplete chunks"):
        api.export_and_download(
            MagicMock(),
            TEST_BASE_URL,
            TEST_EXPORT_PATH,
            TEST_RESULT_BASE,
            TEST_EXPORT_PARAMS,
        )
    mock_download.assert_not_called()


@pytest.mark.parametrize("field_name", ["chunks_failed", "chunks_cancelled"])
def test_export_and_download_rejects_non_list_incomplete_chunks(
    mocker,
    field_name,
):
    # Arrange
    mocker.patch.object(api, "_initiate_export", return_value="export-uuid")
    mocker.patch.object(
        api,
        "_get_export_status",
        return_value={
            "status": "FINISHED",
            "chunks_available": [1],
            field_name: None,
        },
    )

    # Act and assert
    with pytest.raises(TypeError, match=rf"{field_name} returned"):
        api.export_and_download(
            MagicMock(),
            TEST_BASE_URL,
            TEST_EXPORT_PATH,
            TEST_RESULT_BASE,
            TEST_EXPORT_PARAMS,
        )


def test_export_and_download_times_out_without_sleeping_after_final_poll(mocker):
    # Arrange
    mocker.patch.object(api, "_MAX_POLL_ATTEMPTS", 2)
    mocker.patch.object(api, "_EXPORT_POLL_INTERVAL", 1)
    mocker.patch.object(api, "_initiate_export", return_value="export-uuid")
    mock_status = mocker.patch.object(
        api,
        "_get_export_status",
        return_value={"status": "PROCESSING"},
    )
    mock_sleep = mocker.patch.object(api.time, "sleep")

    # Act and assert
    with pytest.raises(TimeoutError, match="did not finish after 2 polls"):
        api.export_and_download(
            MagicMock(),
            TEST_BASE_URL,
            TEST_EXPORT_PATH,
            TEST_RESULT_BASE,
            TEST_EXPORT_PARAMS,
        )
    assert mock_status.call_count == 2
    mock_sleep.assert_called_once_with(1)


def test_initiate_export_propagates_http_errors():
    # Arrange
    session = MagicMock()
    response = session.post.return_value
    response.raise_for_status.side_effect = requests.HTTPError("forbidden")

    # Act and assert
    with pytest.raises(requests.HTTPError, match="forbidden"):
        api._initiate_export(
            session,
            TEST_BASE_URL,
            TEST_EXPORT_PATH,
            TEST_EXPORT_PARAMS,
        )


def test_download_chunk_rejects_non_list_payload():
    # Arrange
    session = MagicMock()
    session.get.return_value.json.return_value = {"unexpected": "object"}

    # Act and assert
    with pytest.raises(TypeError, match="expected a list"):
        api._download_chunk(
            session,
            TEST_BASE_URL,
            TEST_RESULT_BASE,
            "export-uuid",
            1,
        )
