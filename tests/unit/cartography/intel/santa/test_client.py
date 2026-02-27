import io
import zipfile
from unittest.mock import Mock
from unittest.mock import patch

import pytest
import requests

from cartography.intel.santa.client import SantaEventExportEndpointUnavailable
from cartography.intel.santa.client import ZentralSantaClient


def _build_zip_blob(files: dict[str, str]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        for filename, content in files.items():
            archive.writestr(filename, content)
    return buffer.getvalue()


def _response(
    status_code: int,
    json_data: dict | None = None,
    content: bytes | None = None,
) -> Mock:
    response = Mock()
    response.status_code = status_code
    response.json.return_value = json_data or {}
    response.content = content or b""

    if status_code >= 400:
        response.raise_for_status.side_effect = requests.HTTPError(
            f"HTTP {status_code}"
        )
    else:
        response.raise_for_status.return_value = None
    return response


@patch("cartography.intel.santa.client.requests.Session")
def test_export_machine_snapshots_poll_and_parse_jsonl(mock_session: Mock) -> None:
    session = Mock()
    mock_session.return_value = session

    zip_blob = _build_zip_blob(
        {
            "santa.jsonl": (
                '{"serial_number": "C02ABC123", "system_info": {"hostname": "donut-mac"}}\n'
                '{"serial_number": "C02DEF456", "system_info": {"hostname": "lisa-mac"}}\n'
            )
        }
    )

    session.post.return_value = _response(
        201,
        {"task_result_url": "/api/task_result/11111111-1111-1111-1111-111111111111/"},
    )
    session.get.side_effect = [
        _response(
            200,
            {
                "id": "11111111-1111-1111-1111-111111111111",
                "status": "PENDING",
                "unready": True,
            },
        ),
        _response(
            200,
            {
                "id": "11111111-1111-1111-1111-111111111111",
                "status": "SUCCESS",
                "unready": False,
                "download_url": "/api/task_result/11111111-1111-1111-1111-111111111111/download/",
            },
        ),
        _response(200, content=zip_blob),
    ]

    client = ZentralSantaClient(
        base_url="https://zentral.example.com",
        token="test-token",
        request_timeout=5,
        poll_interval_seconds=0,
    )

    rows = list(client.export_machine_snapshots("Santa"))

    assert rows == [
        {"serial_number": "C02ABC123", "system_info": {"hostname": "donut-mac"}},
        {"serial_number": "C02DEF456", "system_info": {"hostname": "lisa-mac"}},
    ]

    session.post.assert_called_once_with(
        "https://zentral.example.com/api/inventory/machines/export_snapshots/",
        params={"source_name": "Santa"},
        timeout=(5, 5),
    )
    assert session.get.call_count == 3


@patch("cartography.intel.santa.client.requests.Session")
def test_export_santa_events_poll_and_parse_csv(mock_session: Mock) -> None:
    session = Mock()
    mock_session.return_value = session

    zip_blob = _build_zip_blob(
        {
            "events.csv": (
                "machine_serial_number;bundle_id;bundle_version\n"
                "C02ABC123;com.apple.Terminal;2.14\n"
            )
        }
    )

    session.post.return_value = _response(
        201,
        {"task_result_url": "/api/task_result/22222222-2222-2222-2222-222222222222/"},
    )
    session.get.side_effect = [
        _response(
            200,
            {
                "id": "22222222-2222-2222-2222-222222222222",
                "status": "SUCCESS",
                "unready": False,
                "download_url": "/api/task_result/22222222-2222-2222-2222-222222222222/download/",
            },
        ),
        _response(200, content=zip_blob),
    ]

    client = ZentralSantaClient(
        base_url="https://zentral.example.com",
        token="test-token",
        request_timeout=5,
        poll_interval_seconds=0,
    )

    rows = list(client.export_santa_events("Santa"))

    assert rows == [
        {
            "machine_serial_number": "C02ABC123",
            "bundle_id": "com.apple.Terminal",
            "bundle_version": "2.14",
        }
    ]

    session.post.assert_called_once_with(
        "https://zentral.example.com/api/santa/events/export/",
        params={"export_format": "zip", "source_name": "Santa"},
        timeout=(5, 5),
    )


@patch("cartography.intel.santa.client.requests.Session")
def test_export_santa_events_fail_fast_when_endpoint_is_missing(
    mock_session: Mock,
) -> None:
    session = Mock()
    mock_session.return_value = session
    session.post.return_value = _response(404)

    client = ZentralSantaClient(
        base_url="https://zentral.example.com",
        token="test-token",
        request_timeout=5,
        poll_interval_seconds=0,
    )

    with pytest.raises(SantaEventExportEndpointUnavailable):
        list(client.export_santa_events("Santa"))
