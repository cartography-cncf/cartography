from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.databricks.storage_configs
from tests.data.databricks.account import DATABRICKS_ACCOUNT_ID
from tests.data.databricks.storage_configs import DATABRICKS_STORAGE_CONFIG_BUCKET
from tests.data.databricks.storage_configs import DATABRICKS_STORAGE_CONFIGS
from tests.integration.cartography.intel.databricks.test_account import (
    _ensure_local_neo4j_has_test_account,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


def _seed_s3_bucket(neo4j_session):
    neo4j_session.run(
        "MERGE (b:AWSS3Bucket {name: $name}) SET b.lastupdated = $tag",
        name=DATABRICKS_STORAGE_CONFIG_BUCKET,
        tag=TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.databricks.storage_configs,
    "get",
    return_value=DATABRICKS_STORAGE_CONFIGS,
)
def test_load_databricks_storage_configs(mock_get, neo4j_session):
    api_session = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ACCOUNT_ID": DATABRICKS_ACCOUNT_ID,
    }
    _ensure_local_neo4j_has_test_account(neo4j_session)
    _seed_s3_bucket(neo4j_session)

    cartography.intel.databricks.storage_configs.sync(
        neo4j_session,
        api_session,
        DATABRICKS_ACCOUNT_ID,
        common_job_parameters,
    )

    assert check_nodes(
        neo4j_session,
        "DatabricksStorageConfig",
        ["storage_configuration_id", "root_bucket_name"],
    ) == {
        ("stg-abc-123", DATABRICKS_STORAGE_CONFIG_BUCKET),
        ("stg-def-456", "some-other-bucket"),
    }

    # StorageConfig -> Account RESOURCE
    assert check_rels(
        neo4j_session,
        "DatabricksStorageConfig",
        "storage_configuration_id",
        "DatabricksAccount",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        ("stg-abc-123", DATABRICKS_ACCOUNT_ID),
        ("stg-def-456", DATABRICKS_ACCOUNT_ID),
    }

    # StorageConfig -> AWSS3Bucket BACKED_BY (only forms for the seeded bucket)
    assert check_rels(
        neo4j_session,
        "DatabricksStorageConfig",
        "storage_configuration_id",
        "AWSS3Bucket",
        "name",
        "BACKED_BY",
        rel_direction_right=True,
    ) == {("stg-abc-123", DATABRICKS_STORAGE_CONFIG_BUCKET)}
