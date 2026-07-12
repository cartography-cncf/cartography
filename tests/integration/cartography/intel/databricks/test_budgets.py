from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.databricks.budgets
from tests.data.databricks.account import DATABRICKS_ACCOUNT_ID
from tests.data.databricks.budgets import DATABRICKS_BUDGETS
from tests.integration.cartography.intel.databricks.test_account import (
    _ensure_local_neo4j_has_test_account,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


@patch.object(
    cartography.intel.databricks.budgets,
    "get",
    return_value=DATABRICKS_BUDGETS,
)
def test_load_databricks_budgets(mock_get, neo4j_session):
    api_session = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ACCOUNT_ID": DATABRICKS_ACCOUNT_ID,
    }
    _ensure_local_neo4j_has_test_account(neo4j_session)

    cartography.intel.databricks.budgets.sync(
        neo4j_session,
        api_session,
        DATABRICKS_ACCOUNT_ID,
        common_job_parameters,
    )

    assert check_nodes(
        neo4j_session,
        "DatabricksBudget",
        ["budget_configuration_id", "display_name"],
    ) == {
        ("budget-abc-123", "monthly-prod-budget"),
        ("budget-def-456", "monthly-dev-budget"),
    }

    # Budget -> Account RESOURCE
    assert check_rels(
        neo4j_session,
        "DatabricksBudget",
        "budget_configuration_id",
        "DatabricksAccount",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        ("budget-abc-123", DATABRICKS_ACCOUNT_ID),
        ("budget-def-456", DATABRICKS_ACCOUNT_ID),
    }
