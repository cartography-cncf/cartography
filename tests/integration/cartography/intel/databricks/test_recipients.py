from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.databricks.recipients
from tests.data.databricks.metastore import DATABRICKS_METASTORE_ID
from tests.data.databricks.recipients import DATABRICKS_RECIPIENTS
from tests.data.databricks.recipients import RECIPIENT_DB_ID
from tests.data.databricks.recipients import RECIPIENT_TOKEN_ID
from tests.data.databricks.workspace import DATABRICKS_WORKSPACE_ID
from tests.integration.cartography.intel.databricks.test_metastores import (
    _ensure_local_neo4j_has_test_metastore,
)
from tests.integration.cartography.intel.databricks.test_workspaces import (
    _ensure_local_neo4j_has_test_workspace,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


def _ensure_local_neo4j_has_test_recipients(neo4j_session):
    cartography.intel.databricks.recipients.load_recipients(
        neo4j_session,
        cartography.intel.databricks.recipients.transform(
            DATABRICKS_RECIPIENTS, DATABRICKS_METASTORE_ID
        ),
        DATABRICKS_WORKSPACE_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.databricks.recipients,
    "get",
    return_value=DATABRICKS_RECIPIENTS,
)
def test_load_databricks_recipients(mock_get, neo4j_session):
    api_session = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "WORKSPACE_ID": DATABRICKS_WORKSPACE_ID,
    }
    _ensure_local_neo4j_has_test_workspace(neo4j_session)
    _ensure_local_neo4j_has_test_metastore(neo4j_session)

    cartography.intel.databricks.recipients.sync(
        neo4j_session,
        api_session,
        DATABRICKS_WORKSPACE_ID,
        DATABRICKS_METASTORE_ID,
        common_job_parameters,
    )

    assert check_nodes(
        neo4j_session,
        "DatabricksRecipient",
        ["id", "name", "authentication_type"],
    ) == {
        (RECIPIENT_TOKEN_ID, "carto_test_recipient", "TOKEN"),
        (RECIPIENT_DB_ID, "partner_account", "DATABRICKS"),
    }

    assert check_rels(
        neo4j_session,
        "DatabricksRecipient",
        "id",
        "DatabricksWorkspace",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        (RECIPIENT_TOKEN_ID, DATABRICKS_WORKSPACE_ID),
        (RECIPIENT_DB_ID, DATABRICKS_WORKSPACE_ID),
    }

    assert check_rels(
        neo4j_session,
        "DatabricksMetastore",
        "id",
        "DatabricksRecipient",
        "id",
        "CONTAINS",
        rel_direction_right=True,
    ) == {
        (DATABRICKS_METASTORE_ID, RECIPIENT_TOKEN_ID),
        (DATABRICKS_METASTORE_ID, RECIPIENT_DB_ID),
    }
