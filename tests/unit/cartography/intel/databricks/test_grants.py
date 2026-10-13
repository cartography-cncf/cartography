from unittest.mock import Mock

import pytest
import requests

import cartography.intel.databricks.grants
from tests.data.databricks.metastore import DATABRICKS_METASTORE_ID


def _uc_id(full_name):
    return f"{DATABRICKS_METASTORE_ID}/{full_name}"


def _http_error(status_code):
    response = Mock(spec=requests.Response)
    response.status_code = status_code
    return requests.HTTPError(response=response)


def test_grants_get_skips_system_registered_model_keeps_complete():
    """A 400 on a `system`-catalog registered_model is the known non-grantable
    case: it is skipped, the remaining securables still load their grants, and
    the read stays complete (it has no HAS_PRIVILEGE edges, so cleanup may run)."""
    # Arrange
    securables = [
        {
            "id": _uc_id("system.ai.model"),
            "full_name": "system.ai.model",
            "securable_type": "registered_model",
        },
        {
            "id": _uc_id("prod"),
            "full_name": "prod",
            "securable_type": "catalog",
        },
    ]
    api_session = Mock()
    api_session.uc_list.side_effect = [
        _http_error(400),
        [{"principal": "jeremy@subimage.io", "privileges": ["USE_CATALOG"]}],
    ]

    # Act
    grants, complete = cartography.intel.databricks.grants.get(api_session, securables)

    # Assert
    assert complete is True
    assert grants == [
        {
            "principal": "jeremy@subimage.io",
            "securable_id": _uc_id("prod"),
            "privileges": ["USE_CATALOG"],
        }
    ]


@pytest.mark.parametrize(
    "status_code",
    [
        # A 400 on a securable that is NOT the known non-grantable case (e.g. a
        # real catalog that may already hold grants) is a genuine BAD_REQUEST:
        # it must abort rather than be swallowed and silently disable cleanup.
        pytest.param(400, id="unexpected_400_on_catalog"),
        # A non-skippable status (e.g. 500) must abort so cleanup never runs on
        # partial data.
        pytest.param(500, id="server_error_500"),
    ],
)
def test_grants_get_http_error_propagates(status_code):
    """HTTP errors that are not the known skippable cases must propagate so
    cleanup never runs on partial data."""
    # Arrange
    securables = [
        {
            "id": _uc_id("prod"),
            "full_name": "prod",
            "securable_type": "catalog",
        },
    ]
    api_session = Mock()
    api_session.uc_list.side_effect = _http_error(status_code)

    # Act and assert
    with pytest.raises(requests.HTTPError):
        cartography.intel.databricks.grants.get(api_session, securables)


def test_grants_get_forbidden_securable_flags_incomplete():
    """A 403/404 securable may hold grants we could not read, so the read is
    flagged incomplete (so the caller skips cleanup) while the remaining
    securables still load their grants."""
    # Arrange
    securables = [
        {
            "id": _uc_id("locked"),
            "full_name": "locked",
            "securable_type": "catalog",
        },
        {
            "id": _uc_id("prod"),
            "full_name": "prod",
            "securable_type": "catalog",
        },
    ]
    api_session = Mock()
    api_session.uc_list.side_effect = [
        _http_error(403),
        [{"principal": "jeremy@subimage.io", "privileges": ["USE_CATALOG"]}],
    ]

    # Act
    grants, complete = cartography.intel.databricks.grants.get(api_session, securables)

    # Assert
    assert complete is False
    assert grants == [
        {
            "principal": "jeremy@subimage.io",
            "securable_id": _uc_id("prod"),
            "privileges": ["USE_CATALOG"],
        }
    ]
