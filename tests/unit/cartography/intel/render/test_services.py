from unittest.mock import Mock

import pytest
import requests

from cartography.intel.render.services import build_latest_deploy_rows
from cartography.intel.render.services import DEPLOY_FETCH_FAILED
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


def test_get_latest_deploys_marks_failed_fetch_distinctly_from_no_deploys(caplog):
    """
    A transient fetch failure must be distinguishable from "this service genuinely has
    no deploys yet" (a real None) - otherwise a caller can't tell the difference
    between "null this out, that's accurate" and "leave whatever was there alone".
    """
    session = Mock()
    session.get.side_effect = requests.exceptions.HTTPError("not found")

    result = get_latest_deploys(session, [{"id": SERVICE_ID}])

    assert result == {SERVICE_ID: DEPLOY_FETCH_FAILED}
    assert "latest deploy fetch failed" in caplog.text
    assert SERVICE_ID in caplog.text


def test_get_latest_deploys_reraises_json_decode_error_without_attribute_lookup():
    """
    Catching `except ValueError` (rather than `except requests.exceptions.
    JSONDecodeError`) must still re-raise a real JSONDecodeError, and must not depend
    on that attribute existing on every supported requests version.
    """
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


def test_build_latest_deploy_rows_includes_a_row_for_a_successful_deploy():
    rows = build_latest_deploy_rows(
        {
            SERVICE_ID: {
                "id": "dep-1",
                "status": "live",
                "trigger": "manual",
                "createdAt": "2026-01-01T00:00:00Z",
                "finishedAt": "2026-01-01T00:05:00Z",
                "commit": {"message": "fix bug"},
                "image": {"ref": "myimage:latest"},
            },
        },
    )

    assert rows == [
        {
            "id": SERVICE_ID,
            "latestDeployId": "dep-1",
            "latestDeployStatus": "live",
            "latestDeployTrigger": "manual",
            "latestDeployCreatedAt": "2026-01-01T00:00:00Z",
            "latestDeployFinishedAt": "2026-01-01T00:05:00Z",
            "latestDeployCommitMessage": "fix bug",
            "latestDeployImageRef": "myimage:latest",
        },
    ]


def test_build_latest_deploy_rows_includes_a_null_row_when_genuinely_no_deploys():
    """
    A confirmed "no deploys yet" result (a real None, not DEPLOY_FETCH_FAILED) is
    accurate current state and must still be loaded, nulling out any stale deploy data
    from before the service's first-ever deploy was rolled back/removed.
    """
    rows = build_latest_deploy_rows({SERVICE_ID: None})

    assert rows == [
        {
            "id": SERVICE_ID,
            "latestDeployId": None,
            "latestDeployStatus": None,
            "latestDeployTrigger": None,
            "latestDeployCreatedAt": None,
            "latestDeployFinishedAt": None,
            "latestDeployCommitMessage": None,
            "latestDeployImageRef": None,
        },
    ]


def test_build_latest_deploy_rows_excludes_a_service_whose_fetch_failed():
    """
    The whole point of DEPLOY_FETCH_FAILED: a service in this state must produce no
    row at all, so the follow-up load() call never mentions it and its existing
    latestDeploy* properties survive untouched.
    """
    rows = build_latest_deploy_rows({SERVICE_ID: DEPLOY_FETCH_FAILED})

    assert rows == []
