from unittest.mock import Mock
from unittest.mock import patch

import pytest
import requests

import cartography.intel.databricks.ip_access_lists
from tests.data.databricks.ip_access_lists import DATABRICKS_IP_ACCESS_LISTS
from tests.data.databricks.workspace import DATABRICKS_WORKSPACE_ID
from tests.data.databricks.workspace import scoped
from tests.integration.cartography.intel.databricks.test_workspaces import (
    _ensure_local_neo4j_has_test_workspace,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


@patch.object(
    cartography.intel.databricks.ip_access_lists,
    "get",
    return_value=DATABRICKS_IP_ACCESS_LISTS,
)
def test_load_databricks_ip_access_lists(mock_get, neo4j_session):
    api_session = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "WORKSPACE_ID": DATABRICKS_WORKSPACE_ID,
    }
    _ensure_local_neo4j_has_test_workspace(neo4j_session)

    cartography.intel.databricks.ip_access_lists.sync(
        neo4j_session,
        api_session,
        DATABRICKS_WORKSPACE_ID,
        common_job_parameters,
    )

    assert check_nodes(
        neo4j_session,
        "DatabricksIpAccessList",
        ["id", "list_id", "label", "list_type", "enabled"],
    ) == {
        (
            scoped("0303-iplist-aaaa"),
            "0303-iplist-aaaa",
            "office",
            "ALLOW",
            True,
        ),
        (
            scoped("0303-iplist-bbbb"),
            "0303-iplist-bbbb",
            "blocked-ranges",
            "BLOCK",
            False,
        ),
    }

    assert check_rels(
        neo4j_session,
        "DatabricksIpAccessList",
        "id",
        "DatabricksWorkspace",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        (scoped("0303-iplist-aaaa"), DATABRICKS_WORKSPACE_ID),
        (scoped("0303-iplist-bbbb"), DATABRICKS_WORKSPACE_ID),
    }


def test_ip_access_lists_feature_disabled_returns_empty():
    """Standard-tier workspaces return 404 FEATURE_DISABLED; treat as no lists."""
    api_session = Mock()
    response = Mock(spec=requests.Response)
    response.status_code = 404
    response.json.return_value = {
        "error_code": "FEATURE_DISABLED",
        "message": "IP access list is not available in the pricing tier of this workspace",
    }
    api_session.get.side_effect = requests.HTTPError(response=response)

    assert cartography.intel.databricks.ip_access_lists.get(api_session) == []


def test_ip_access_lists_other_http_error_propagates():
    """Any other HTTP error must surface; we only swallow FEATURE_DISABLED."""
    api_session = Mock()
    response = Mock(spec=requests.Response)
    response.status_code = 500
    response.json.return_value = {"error_code": "INTERNAL_ERROR", "message": "boom"}
    api_session.get.side_effect = requests.HTTPError(response=response)

    with pytest.raises(requests.HTTPError):
        cartography.intel.databricks.ip_access_lists.get(api_session)
