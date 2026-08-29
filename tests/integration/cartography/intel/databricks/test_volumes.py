from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.databricks.volumes
from tests.data.databricks.metastore import DATABRICKS_METASTORE_ID
from tests.data.databricks.volumes import DATABRICKS_VOLUME_S3_BUCKET
from tests.data.databricks.volumes import DATABRICKS_VOLUMES
from tests.data.databricks.workspace import DATABRICKS_WORKSPACE_ID
from tests.integration.cartography.intel.databricks.test_catalogs import (
    _ensure_local_neo4j_has_test_catalogs,
)
from tests.integration.cartography.intel.databricks.test_metastores import (
    _ensure_local_neo4j_has_test_metastore,
)
from tests.integration.cartography.intel.databricks.test_schemas import (
    _ensure_local_neo4j_has_test_schemas,
)
from tests.integration.cartography.intel.databricks.test_workspaces import (
    _ensure_local_neo4j_has_test_workspace,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


def _uc_id(full_name):
    return f"{DATABRICKS_METASTORE_ID}/{full_name}"


@patch.object(
    cartography.intel.databricks.volumes,
    "get",
    return_value=DATABRICKS_VOLUMES,
)
def test_load_databricks_volumes(mock_get, neo4j_session):
    api_session = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "WORKSPACE_ID": DATABRICKS_WORKSPACE_ID,
    }
    _ensure_local_neo4j_has_test_workspace(neo4j_session)
    _ensure_local_neo4j_has_test_metastore(neo4j_session)
    _ensure_local_neo4j_has_test_catalogs(neo4j_session)
    _ensure_local_neo4j_has_test_schemas(neo4j_session)
    neo4j_session.run(
        "MERGE (b:AWSS3Bucket {name: $name}) SET b.lastupdated = $tag",
        name=DATABRICKS_VOLUME_S3_BUCKET,
        tag=TEST_UPDATE_TAG,
    )

    cartography.intel.databricks.volumes.sync(
        neo4j_session,
        api_session,
        DATABRICKS_WORKSPACE_ID,
        [],
        common_job_parameters,
    )

    assert check_nodes(
        neo4j_session,
        "DatabricksVolume",
        ["id", "name", "volume_type"],
    ) == {(_uc_id("prod.finance.landing"), "landing", "EXTERNAL")}

    # Schema -> Volume CONTAINS
    assert check_rels(
        neo4j_session,
        "DatabricksSchema",
        "id",
        "DatabricksVolume",
        "id",
        "CONTAINS",
        rel_direction_right=True,
    ) == {(_uc_id("prod.finance"), _uc_id("prod.finance.landing"))}

    # Volume -> AWSS3Bucket BACKED_BY
    assert check_rels(
        neo4j_session,
        "DatabricksVolume",
        "id",
        "AWSS3Bucket",
        "name",
        "BACKED_BY",
        rel_direction_right=True,
    ) == {(_uc_id("prod.finance.landing"), DATABRICKS_VOLUME_S3_BUCKET)}
