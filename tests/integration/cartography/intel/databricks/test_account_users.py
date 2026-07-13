from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.databricks.account_users
from tests.data.databricks.account import account_scoped
from tests.data.databricks.account import DATABRICKS_ACCOUNT_ID
from tests.data.databricks.account_users import DATABRICKS_ACCOUNT_USERS
from tests.integration.cartography.intel.databricks.test_account import (
    _ensure_local_neo4j_has_test_account,
)
from tests.integration.cartography.intel.databricks.test_account_groups import (
    _ensure_local_neo4j_has_test_account_groups,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


def _ensure_local_neo4j_has_test_account_users(neo4j_session):
    cartography.intel.databricks.account_users.load_users(
        neo4j_session,
        cartography.intel.databricks.account_users.transform(
            DATABRICKS_ACCOUNT_USERS, DATABRICKS_ACCOUNT_ID
        ),
        DATABRICKS_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.databricks.account_users,
    "get",
    return_value=DATABRICKS_ACCOUNT_USERS,
)
def test_load_databricks_account_users(mock_get, neo4j_session):
    # Arrange
    api_session = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ACCOUNT_ID": DATABRICKS_ACCOUNT_ID,
    }
    _ensure_local_neo4j_has_test_account(neo4j_session)
    _ensure_local_neo4j_has_test_account_groups(neo4j_session)

    # Act
    cartography.intel.databricks.account_users.sync(
        neo4j_session,
        api_session,
        DATABRICKS_ACCOUNT_ID,
        common_job_parameters,
    )

    # Assert user nodes
    assert check_nodes(
        neo4j_session,
        "DatabricksAccountUser",
        ["id", "scim_id", "user_name", "email"],
    ) == {
        (
            account_scoped("410001"),
            "410001",
            "jeremy@subimage.io",
            "jeremy@subimage.io",
        ),
        (
            account_scoped("410002"),
            "410002",
            "kunaal@subimage.io",
            "kunaal@subimage.io",
        ),
    }

    # UserAccount ontology label is applied.
    assert check_nodes(neo4j_session, "UserAccount", ["id"]) >= {
        (account_scoped("410001"),),
        (account_scoped("410002"),),
    }

    # Assert User -> Account RESOURCE
    assert check_rels(
        neo4j_session,
        "DatabricksAccountUser",
        "id",
        "DatabricksAccount",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        (account_scoped("410001"), DATABRICKS_ACCOUNT_ID),
        (account_scoped("410002"), DATABRICKS_ACCOUNT_ID),
    }

    # Assert User -> Group MEMBER_OF
    assert check_rels(
        neo4j_session,
        "DatabricksAccountUser",
        "id",
        "DatabricksAccountGroup",
        "id",
        "MEMBER_OF",
        rel_direction_right=True,
    ) == {
        (account_scoped("410001"), account_scoped("310001")),
        (account_scoped("410001"), account_scoped("310002")),
        (account_scoped("410002"), account_scoped("310001")),
    }
