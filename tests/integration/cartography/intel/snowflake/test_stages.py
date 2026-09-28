from unittest.mock import patch

import cartography.intel.snowflake.stages
from tests.data.snowflake.account import SNOWFLAKE_ACCOUNT_ID
from tests.data.snowflake.stages import SNOWFLAKE_STAGE_AZURE_STORAGE_ACCOUNT
from tests.data.snowflake.stages import SNOWFLAKE_STAGE_GCS_BUCKET
from tests.data.snowflake.stages import SNOWFLAKE_STAGE_S3_BUCKET
from tests.data.snowflake.stages import SNOWFLAKE_STAGES
from tests.integration.cartography.intel.snowflake.test_account import build_test_client
from tests.integration.cartography.intel.snowflake.test_account import TEST_UPDATE_TAG
from tests.integration.cartography.intel.snowflake.test_schemas import (
    _ensure_local_neo4j_has_test_schemas,
)
from tests.integration.cartography.intel.snowflake.test_schemas import (
    KWIK_E_MART_SCHEMA_ID,
)
from tests.integration.cartography.intel.snowflake.test_schemas import (
    NUCLEAR_PLANT_SCHEMA_ID,
)
from tests.integration.cartography.intel.snowflake.test_schemas import TEST_SCHEMAS
from tests.integration.cartography.intel.snowflake.test_storage_integrations import (
    _ensure_local_neo4j_has_test_storage_integrations,
)
from tests.integration.cartography.intel.snowflake.test_storage_integrations import (
    PLANT_S3_INTEGRATION_ID,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

REACTOR_LOG_STAGE_ID = (
    "SPRINGFIELD.NUCLEAR/stage/SPRINGFIELD.NUCLEAR_PLANT.REACTOR_LOG_STAGE"
)
SCRATCH_STAGE_ID = "SPRINGFIELD.NUCLEAR/stage/SPRINGFIELD.NUCLEAR_PLANT.SCRATCH_STAGE"
DONUT_ARCHIVE_STAGE_ID = (
    "SPRINGFIELD.NUCLEAR/stage/SPRINGFIELD.KWIK_E_MART.DONUT_ARCHIVE_STAGE"
)
SQUISHEE_BLOB_STAGE_ID = "SPRINGFIELD.NUCLEAR/stage/MONORAIL.PUBLIC.SQUISHEE_BLOB_STAGE"


def _seed_cloud_storage(neo4j_session) -> None:
    """Seed the buckets and storage account the aws, gcp and azure modules would own."""
    neo4j_session.run(
        "MERGE (b:AWSS3Bucket{name: $s3}) SET b.lastupdated = $tag "
        "MERGE (g:GCPBucket{id: $gcs}) SET g.lastupdated = $tag "
        "MERGE (a:AzureStorageAccount{name: $azure}) SET a.lastupdated = $tag",
        s3=SNOWFLAKE_STAGE_S3_BUCKET,
        gcs=SNOWFLAKE_STAGE_GCS_BUCKET,
        azure=SNOWFLAKE_STAGE_AZURE_STORAGE_ACCOUNT,
        tag=TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.snowflake.stages,
    "get",
    return_value=(SNOWFLAKE_STAGES, True),
)
def test_sync_snowflake_stages(mock_get, neo4j_session):
    # Arrange
    _ensure_local_neo4j_has_test_schemas(neo4j_session)
    _ensure_local_neo4j_has_test_storage_integrations(neo4j_session)
    _seed_cloud_storage(neo4j_session)

    # Act
    complete = cartography.intel.snowflake.stages.sync(
        neo4j_session,
        build_test_client(),
        TEST_SCHEMAS,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "ACCOUNT_ID": SNOWFLAKE_ACCOUNT_ID},
    )

    # Assert: the external/internal discriminator is derived from the url, and a stage
    # holding its own cloud credentials is distinguishable from one delegating to a
    # storage integration.
    assert complete is True
    assert check_nodes(
        neo4j_session,
        "SnowflakeStage",
        ["id", "name", "is_external", "has_credentials", "storage_integration"],
    ) == {
        (
            REACTOR_LOG_STAGE_ID,
            "REACTOR_LOG_STAGE",
            "true",
            False,
            "PLANT_S3_INTEGRATION",
        ),
        (SCRATCH_STAGE_ID, "SCRATCH_STAGE", "false", False, None),
        (DONUT_ARCHIVE_STAGE_ID, "DONUT_ARCHIVE_STAGE", "true", True, None),
        (SQUISHEE_BLOB_STAGE_ID, "SQUISHEE_BLOB_STAGE", "true", False, None),
    }
    # The conditional ontology labels split by that discriminator: external stages are
    # object storage, the internal one is file storage.
    assert check_nodes(neo4j_session, "ObjectStorage", ["id"]) >= {
        (REACTOR_LOG_STAGE_ID,),
        (DONUT_ARCHIVE_STAGE_ID,),
        (SQUISHEE_BLOB_STAGE_ID,),
    }
    assert (SCRATCH_STAGE_ID,) not in check_nodes(
        neo4j_session, "ObjectStorage", ["id"]
    )
    assert (SCRATCH_STAGE_ID,) in check_nodes(neo4j_session, "FileStorage", ["id"])

    assert check_rels(
        neo4j_session,
        "SnowflakeStage",
        "id",
        "SnowflakeSchema",
        "id",
        "CONTAINS",
        rel_direction_right=False,
    ) >= {
        (REACTOR_LOG_STAGE_ID, NUCLEAR_PLANT_SCHEMA_ID),
        (SCRATCH_STAGE_ID, NUCLEAR_PLANT_SCHEMA_ID),
        (DONUT_ARCHIVE_STAGE_ID, KWIK_E_MART_SCHEMA_ID),
    }
    assert check_rels(
        neo4j_session,
        "SnowflakeStage",
        "id",
        "SnowflakeStorageIntegration",
        "id",
        "USES_INTEGRATION",
        rel_direction_right=True,
    ) == {(REACTOR_LOG_STAGE_ID, PLANT_S3_INTEGRATION_ID)}

    # The cross-cloud payoff: each external stage is joined to the concrete bucket or
    # storage account it reads and writes.
    assert check_rels(
        neo4j_session,
        "SnowflakeStage",
        "id",
        "AWSS3Bucket",
        "name",
        "BACKED_BY",
        rel_direction_right=True,
    ) == {(REACTOR_LOG_STAGE_ID, SNOWFLAKE_STAGE_S3_BUCKET)}
    assert check_rels(
        neo4j_session,
        "SnowflakeStage",
        "id",
        "GCPBucket",
        "id",
        "BACKED_BY",
        rel_direction_right=True,
    ) == {(DONUT_ARCHIVE_STAGE_ID, SNOWFLAKE_STAGE_GCS_BUCKET)}
    assert check_rels(
        neo4j_session,
        "SnowflakeStage",
        "id",
        "AzureStorageAccount",
        "name",
        "BACKED_BY",
        rel_direction_right=True,
    ) == {(SQUISHEE_BLOB_STAGE_ID, SNOWFLAKE_STAGE_AZURE_STORAGE_ACCOUNT)}
