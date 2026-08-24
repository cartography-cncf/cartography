from unittest.mock import Mock
from unittest.mock import patch

import pytest
import requests
from scaleway_core.api import ScalewayException

from cartography.intel.scaleway.cockpit.cockpit import get
from cartography.intel.scaleway.cockpit.cockpit import transform_cockpits
from cartography.intel.scaleway.cockpit.cockpit import transform_data_sources
from cartography.intel.scaleway.cockpit.cockpit import transform_tokens
from tests.data.scaleway.cockpit import SCALEWAY_COCKPIT_DATA_SOURCES
from tests.data.scaleway.cockpit import SCALEWAY_COCKPIT_PLAN
from tests.data.scaleway.cockpit import SCALEWAY_COCKPIT_TOKENS
from tests.data.scaleway.cockpit import TEST_DATA_SOURCE_ID
from tests.data.scaleway.cockpit import TEST_PROJECT_ID
from tests.data.scaleway.cockpit import TEST_TOKEN_ID

TEST_SKIPPED_PROJECT_ID = "11111111-1111-1111-1111-111111111111"


def _scaleway_exception(status_code: int, text: str) -> ScalewayException:
    response = requests.Response()
    response.status_code = status_code
    response._content = text.encode()
    return ScalewayException(response)


def test_transform_cockpits_uses_project_id_as_node_id():
    rows = transform_cockpits({TEST_PROJECT_ID: SCALEWAY_COCKPIT_PLAN})

    assert rows == {
        TEST_PROJECT_ID: [{"id": TEST_PROJECT_ID, "plan_name": "free"}],
    }


def test_transform_data_sources_groups_by_project():
    rows = transform_data_sources(SCALEWAY_COCKPIT_DATA_SOURCES)

    assert list(rows.keys()) == [TEST_PROJECT_ID]
    assert rows[TEST_PROJECT_ID][0]["id"] == TEST_DATA_SOURCE_ID


def test_transform_tokens_discards_the_secret_key():
    """
    Scaleway's list API returns each token's full secret_key alongside its metadata -
    that value must never reach the graph.
    """
    rows = transform_tokens(SCALEWAY_COCKPIT_TOKENS)

    assert rows[TEST_PROJECT_ID][0]["id"] == TEST_TOKEN_ID
    assert "secret_key" not in rows[TEST_PROJECT_ID][0]


def test_transform_tokens_keeps_scopes():
    rows = transform_tokens(SCALEWAY_COCKPIT_TOKENS)

    assert rows[TEST_PROJECT_ID][0]["scopes"] == ["read_only_metrics", "read_only_logs"]


@patch("cartography.intel.scaleway.cockpit.cockpit.list_all_regions")
@patch("cartography.intel.scaleway.cockpit.cockpit.CockpitV1RegionalAPI")
@patch("cartography.intel.scaleway.cockpit.cockpit.CockpitV1GlobalAPI")
def test_get_skips_one_project_on_scaleway_exception(
    mock_global_api_cls,
    mock_regional_api_cls,
    mock_list_all_regions,
):
    global_api = Mock()
    global_api.get_current_plan.side_effect = [
        _scaleway_exception(403, "permission denied"),
        SCALEWAY_COCKPIT_PLAN,
    ]
    mock_global_api_cls.return_value = global_api
    mock_regional_api_cls.return_value = Mock()
    mock_list_all_regions.side_effect = [
        SCALEWAY_COCKPIT_DATA_SOURCES,
        SCALEWAY_COCKPIT_TOKENS,
    ]

    plan_by_project, data_sources, tokens, completed_project_ids = get(
        Mock(),
        [TEST_SKIPPED_PROJECT_ID, TEST_PROJECT_ID],
    )

    assert plan_by_project == {TEST_PROJECT_ID: SCALEWAY_COCKPIT_PLAN}
    assert data_sources == SCALEWAY_COCKPIT_DATA_SOURCES
    assert tokens == SCALEWAY_COCKPIT_TOKENS
    assert completed_project_ids == [TEST_PROJECT_ID]


@patch("cartography.intel.scaleway.cockpit.cockpit.CockpitV1RegionalAPI")
@patch("cartography.intel.scaleway.cockpit.cockpit.CockpitV1GlobalAPI")
def test_get_raises_unexpected_scaleway_exception(
    mock_global_api_cls,
    mock_regional_api_cls,
):
    global_api = Mock()
    global_api.get_current_plan.side_effect = _scaleway_exception(
        500,
        "internal server error",
    )
    mock_global_api_cls.return_value = global_api
    mock_regional_api_cls.return_value = Mock()

    with pytest.raises(ScalewayException):
        get(Mock(), [TEST_PROJECT_ID])
