from unittest.mock import Mock

import pytest
import requests

from cartography.intel.render.services import get_latest_deploy
from cartography.intel.render.services import get_latest_deploys
from cartography.intel.render.util import BASE_URL

SERVICE_ID = "srv-test001"
DEPLOY = {
    "id": "dep-test001",
    "status": "live",
}


def _response(body):
    mock_response = Mock()
    mock_response.json.return_value = body
    mock_response.raise_for_status.return_value = None
    return mock_response


def test_get_latest_deploy_returns_newest_deploy():
    session = Mock()
    session.get.return_value = _response([{"deploy": DEPLOY, "cursor": "cur-1"}])

    result = get_latest_deploy(session, SERVICE_ID)

    assert result == DEPLOY
    session.get.assert_called_once_with(
        f"{BASE_URL}/services/{SERVICE_ID}/deploys",
        params={"limit": 1},
        timeout=(60, 60),
    )


def test_get_latest_deploy_returns_none_when_service_has_no_deploys():
    session = Mock()
    session.get.return_value = _response([])

    assert get_latest_deploy(session, SERVICE_ID) is None


def test_get_latest_deploy_raises_on_non_list_response():
    session = Mock()
    session.get.return_value = _response({"deploy": DEPLOY})

    with pytest.raises(ValueError):
        get_latest_deploy(session, SERVICE_ID)


def test_get_latest_deploy_raises_on_entry_missing_deploy_key():
    session = Mock()
    session.get.return_value = _response([{"cursor": "cur-1"}])

    with pytest.raises(ValueError):
        get_latest_deploy(session, SERVICE_ID)


def test_get_latest_deploy_raises_on_non_object_deploy():
    session = Mock()
    session.get.return_value = _response([{"deploy": "not-an-object"}])

    with pytest.raises(ValueError):
        get_latest_deploy(session, SERVICE_ID)


def test_get_latest_deploys_returns_none_for_request_exception(caplog):
    session = Mock()
    session.get.side_effect = requests.exceptions.HTTPError("not found")

    result = get_latest_deploys(session, [{"id": SERVICE_ID}])

    assert result == {SERVICE_ID: None}
    assert "latest deploy fetch failed" in caplog.text
    assert SERVICE_ID in caplog.text


def test_get_latest_deploys_reraises_malformed_json():
    response = Mock()
    response.raise_for_status.return_value = None
    response.json.side_effect = requests.exceptions.JSONDecodeError("bad json", "", 0)
    session = Mock()
    session.get.return_value = response

    with pytest.raises(requests.exceptions.JSONDecodeError):
        get_latest_deploys(session, [{"id": SERVICE_ID}])


def test_get_latest_deploys_reraises_malformed_response_shape():
    session = Mock()
    session.get.return_value = _response({"deploy": DEPLOY})

    with pytest.raises(ValueError):
        get_latest_deploys(session, [{"id": SERVICE_ID}])
