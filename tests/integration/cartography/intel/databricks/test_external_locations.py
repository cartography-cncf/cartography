from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.databricks.external_locations
import cartography.intel.databricks.storage_credentials
from tests.data.databricks.external_locations import (
    DATABRICKS_EXTERNAL_LOCATION_S3_BUCKET,
)
from tests.data.databricks.external_locations import DATABRICKS_EXTERNAL_LOCATIONS
from tests.data.databricks.storage_credentials import DATABRICKS_STORAGE_CREDENTIALS
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


def _seed_storage_credentials(neo4j_session):
    cartography.intel.databricks.storage_credentials.load_storage_credentials(
        neo4j_session,
        cartography.intel.databricks.storage_credentials.transform(
            DATABRICKS_STORAGE_CREDENTIALS
        ),
        DATABRICKS_WORKSPACE_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.databricks.external_locations,
    "get",
    return_value=DATABRICKS_EXTERNAL_LOCATIONS,
)
def test_load_databricks_external_locations(mock_get, neo4j_session):
    api_session = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "WORKSPACE_ID": DATABRICKS_WORKSPACE_ID,
    }
    _ensure_local_neo4j_has_test_workspace(neo4j_session)
    _ensure_local_neo4j_has_test_metastore(neo4j_session)
    _seed_storage_credentials(neo4j_session)
    neo4j_session.run(
        "MERGE (b:S3Bucket {name: $name}) SET b.lastupdated = $tag",
        name=DATABRICKS_EXTERNAL_LOCATION_S3_BUCKET,
        tag=TEST_UPDATE_TAG,
    )

    cartography.intel.databricks.external_locations.sync(
        neo4j_session,
        api_session,
        DATABRICKS_WORKSPACE_ID,
        common_job_parameters,
    )

    assert check_nodes(
        neo4j_session,
        "DatabricksExternalLocation",
        ["name", "url"],
    ) == {
        (
            "managed_storage_location",
            f"s3://{DATABRICKS_EXTERNAL_LOCATION_S3_BUCKET}/uc/data",
        ),
    }

    # ExternalLocation -> StorageCredential USES_CREDENTIAL
    assert check_rels(
        neo4j_session,
        "DatabricksExternalLocation",
        "name",
        "DatabricksStorageCredential",
        "name",
        "USES_CREDENTIAL",
        rel_direction_right=True,
    ) == {("managed_storage_location", "aws-uc-storage-cred")}

    # ExternalLocation -> S3Bucket BACKED_BY (parsed from the s3:// url)
    assert check_rels(
        neo4j_session,
        "DatabricksExternalLocation",
        "name",
        "S3Bucket",
        "name",
        "BACKED_BY",
        rel_direction_right=True,
    ) == {("managed_storage_location", DATABRICKS_EXTERNAL_LOCATION_S3_BUCKET)}
