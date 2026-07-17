from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.databricks.shares
from tests.data.databricks.metastore import DATABRICKS_METASTORE_ID
from tests.data.databricks.recipients import RECIPIENT_TOKEN_ID
from tests.data.databricks.shares import DATABRICKS_SHARES
from tests.data.databricks.shares import SHARE_ID
from tests.data.databricks.workspace import DATABRICKS_WORKSPACE_ID
from tests.integration.cartography.intel.databricks.test_metastores import (
    _ensure_local_neo4j_has_test_metastore,
)
from tests.integration.cartography.intel.databricks.test_recipients import (
    _ensure_local_neo4j_has_test_recipients,
)
from tests.integration.cartography.intel.databricks.test_workspaces import (
    _ensure_local_neo4j_has_test_workspace,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


@patch.object(
    cartography.intel.databricks.shares,
    "_recipient_names",
    return_value=["carto_test_recipient"],
)
@patch.object(
    cartography.intel.databricks.shares,
    "get",
    return_value=DATABRICKS_SHARES,
)
def test_load_databricks_shares(mock_get, mock_perms, neo4j_session):
    api_session = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "WORKSPACE_ID": DATABRICKS_WORKSPACE_ID,
    }
    _ensure_local_neo4j_has_test_workspace(neo4j_session)
    _ensure_local_neo4j_has_test_metastore(neo4j_session)
    _ensure_local_neo4j_has_test_recipients(neo4j_session)

    cartography.intel.databricks.shares.sync(
        neo4j_session,
        api_session,
        DATABRICKS_WORKSPACE_ID,
        DATABRICKS_METASTORE_ID,
        common_job_parameters,
    )

    assert check_nodes(neo4j_session, "DatabricksShare", ["id", "name", "owner"]) == {
        (SHARE_ID, "carto_test_share", "jeremy@subimage.io")
    }

    assert check_rels(
        neo4j_session,
        "DatabricksMetastore",
        "id",
        "DatabricksShare",
        "id",
        "CONTAINS",
        rel_direction_right=True,
    ) == {(DATABRICKS_METASTORE_ID, SHARE_ID)}

    # Share -> Recipient SHARED_WITH, from the share's permission assignments.
    assert check_rels(
        neo4j_session,
        "DatabricksShare",
        "id",
        "DatabricksRecipient",
        "id",
        "SHARED_WITH",
        rel_direction_right=True,
    ) == {(SHARE_ID, RECIPIENT_TOKEN_ID)}
