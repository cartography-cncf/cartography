import cartography.intel.databricks.account
from tests.data.databricks.account import DATABRICKS_ACCOUNT
from tests.data.databricks.account import DATABRICKS_ACCOUNT_ID
from tests.integration.util import check_nodes

TEST_UPDATE_TAG = 123456789


def _ensure_local_neo4j_has_test_account(neo4j_session):
    cartography.intel.databricks.account.load(
        neo4j_session,
        cartography.intel.databricks.account.DatabricksAccountSchema(),
        [DATABRICKS_ACCOUNT],
        lastupdated=TEST_UPDATE_TAG,
    )


def test_ensure_local_neo4j_has_test_account(neo4j_session):
    _ensure_local_neo4j_has_test_account(neo4j_session)
    assert check_nodes(neo4j_session, "DatabricksAccount", ["id"]) == {
        (DATABRICKS_ACCOUNT_ID,)
    }
    # Tenant ontology label is applied.
    assert check_nodes(neo4j_session, "Tenant", ["id"]) >= {(DATABRICKS_ACCOUNT_ID,)}
