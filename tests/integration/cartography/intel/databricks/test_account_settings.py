from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.databricks.account_settings
from tests.data.databricks.account import DATABRICKS_ACCOUNT_ID
from tests.data.databricks.account_settings import DATABRICKS_ACCOUNT_SETTINGS
from tests.integration.cartography.intel.databricks.test_account import (
    _ensure_local_neo4j_has_test_account,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


@patch.object(
    cartography.intel.databricks.account_settings,
    "get",
    return_value=DATABRICKS_ACCOUNT_SETTINGS,
)
def test_load_databricks_account_settings(mock_get, neo4j_session):
    api_session = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ACCOUNT_ID": DATABRICKS_ACCOUNT_ID,
    }
    _ensure_local_neo4j_has_test_account(neo4j_session)

    cartography.intel.databricks.account_settings.sync(
        neo4j_session,
        api_session,
        DATABRICKS_ACCOUNT_ID,
        common_job_parameters,
    )

    assert check_nodes(
        neo4j_session,
        "DatabricksAccountSetting",
        ["setting_name", "value"],
    ) == {("personal_compute", "ON")}

    # AccountSetting -> Account RESOURCE
    assert check_rels(
        neo4j_session,
        "DatabricksAccountSetting",
        "setting_name",
        "DatabricksAccount",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {("personal_compute", DATABRICKS_ACCOUNT_ID)}
