from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.databricks.account_groups
from tests.data.databricks.account import account_scoped
from tests.data.databricks.account import DATABRICKS_ACCOUNT_ID
from tests.data.databricks.account_groups import DATABRICKS_ACCOUNT_GROUPS
from tests.integration.cartography.intel.databricks.test_account import (
    _ensure_local_neo4j_has_test_account,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


def _ensure_local_neo4j_has_test_account_groups(neo4j_session):
    cartography.intel.databricks.account_groups.load_groups(
        neo4j_session,
        cartography.intel.databricks.account_groups.transform(
            DATABRICKS_ACCOUNT_GROUPS, DATABRICKS_ACCOUNT_ID
        ),
        DATABRICKS_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.databricks.account_groups,
    "get",
    return_value=DATABRICKS_ACCOUNT_GROUPS,
)
def test_load_databricks_account_groups(mock_get, neo4j_session):
    # Arrange
    api_session = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ACCOUNT_ID": DATABRICKS_ACCOUNT_ID,
    }
    _ensure_local_neo4j_has_test_account(neo4j_session)

    # Act
    cartography.intel.databricks.account_groups.sync(
        neo4j_session,
        api_session,
        DATABRICKS_ACCOUNT_ID,
        common_job_parameters,
    )

    # Assert group nodes
    assert check_nodes(
        neo4j_session, "DatabricksAccountGroup", ["id", "scim_id", "display_name"]
    ) == {
        (account_scoped("310001"), "310001", "account users"),
        (account_scoped("310002"), "310002", "admins"),
    }

    # UserGroup ontology label is applied (matches the workspace-level group).
    assert check_nodes(neo4j_session, "UserGroup", ["id"]) >= {
        (account_scoped("310001"),),
        (account_scoped("310002"),),
    }

    # Assert Group -> Account RESOURCE
    assert check_rels(
        neo4j_session,
        "DatabricksAccountGroup",
        "id",
        "DatabricksAccount",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        (account_scoped("310001"), DATABRICKS_ACCOUNT_ID),
        (account_scoped("310002"), DATABRICKS_ACCOUNT_ID),
    }

    # Assert nested Group -> Group MEMBER_OF (admins is member of account users)
    assert check_rels(
        neo4j_session,
        "DatabricksAccountGroup",
        "id",
        "DatabricksAccountGroup",
        "id",
        "MEMBER_OF",
        rel_direction_right=True,
    ) == {
        (account_scoped("310002"), account_scoped("310001")),
    }
