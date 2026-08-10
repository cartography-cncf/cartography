from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.databricks.account_service_principals
from tests.data.databricks.account import account_scoped
from tests.data.databricks.account import DATABRICKS_ACCOUNT_ID
from tests.data.databricks.account_service_principals import (
    DATABRICKS_ACCOUNT_SERVICE_PRINCIPALS,
)
from tests.integration.cartography.intel.databricks.test_account import (
    _ensure_local_neo4j_has_test_account,
)
from tests.integration.cartography.intel.databricks.test_account_groups import (
    _ensure_local_neo4j_has_test_account_groups,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


def _ensure_local_neo4j_has_test_account_service_principals(neo4j_session):
    cartography.intel.databricks.account_service_principals.load_service_principals(
        neo4j_session,
        cartography.intel.databricks.account_service_principals.transform(
            DATABRICKS_ACCOUNT_SERVICE_PRINCIPALS, DATABRICKS_ACCOUNT_ID
        ),
        DATABRICKS_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.databricks.account_service_principals,
    "get",
    return_value=DATABRICKS_ACCOUNT_SERVICE_PRINCIPALS,
)
def test_load_databricks_account_service_principals(mock_get, neo4j_session):
    # Arrange
    api_session = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ACCOUNT_ID": DATABRICKS_ACCOUNT_ID,
    }
    _ensure_local_neo4j_has_test_account(neo4j_session)
    _ensure_local_neo4j_has_test_account_groups(neo4j_session)

    # Act
    cartography.intel.databricks.account_service_principals.sync(
        neo4j_session,
        api_session,
        DATABRICKS_ACCOUNT_ID,
        common_job_parameters,
    )

    # Assert service principal nodes
    assert check_nodes(
        neo4j_session,
        "DatabricksAccountServicePrincipal",
        ["id", "scim_id", "application_id"],
    ) == {
        (
            account_scoped("510001"),
            "510001",
            "abcd1234-5678-90ab-cdef-1234567890ab",
        ),
    }

    # ServiceAccount ontology label is applied (matches the workspace-level SP).
    assert check_nodes(neo4j_session, "ServiceAccount", ["id"]) >= {
        (account_scoped("510001"),),
    }

    # Assert SP -> Account RESOURCE
    assert check_rels(
        neo4j_session,
        "DatabricksAccountServicePrincipal",
        "id",
        "DatabricksAccount",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        (account_scoped("510001"), DATABRICKS_ACCOUNT_ID),
    }

    # Assert SP -> Group MEMBER_OF
    assert check_rels(
        neo4j_session,
        "DatabricksAccountServicePrincipal",
        "id",
        "DatabricksAccountGroup",
        "id",
        "MEMBER_OF",
        rel_direction_right=True,
    ) == {
        (account_scoped("510001"), account_scoped("310002")),
    }
