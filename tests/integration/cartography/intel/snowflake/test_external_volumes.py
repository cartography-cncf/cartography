from unittest.mock import patch

import cartography.intel.snowflake.external_volumes
from tests.data.snowflake.account import SNOWFLAKE_ACCOUNT_ID
from tests.data.snowflake.external_volumes import SNOWFLAKE_EXTERNAL_VOLUMES
from tests.data.snowflake.external_volumes import SNOWFLAKE_VOLUME_GCS_BUCKET
from tests.data.snowflake.external_volumes import SNOWFLAKE_VOLUME_KMS_KEY_ARN
from tests.data.snowflake.external_volumes import SNOWFLAKE_VOLUME_ROLE_ARN
from tests.data.snowflake.external_volumes import SNOWFLAKE_VOLUME_S3_BUCKET
from tests.integration.cartography.intel.snowflake.test_account import (
    _ensure_local_neo4j_has_test_account,
)
from tests.integration.cartography.intel.snowflake.test_account import build_test_client
from tests.integration.cartography.intel.snowflake.test_account import TEST_UPDATE_TAG
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

MONORAIL_VOLUME_ID = "SPRINGFIELD.NUCLEAR/external_volume/MONORAIL_VOLUME"
DUFF_VOLUME_ID = "SPRINGFIELD.NUCLEAR/external_volume/DUFF_VOLUME"
PRIMARY_S3_LOCATION_ID = (
    "SPRINGFIELD.NUCLEAR/external_volume_storage_location/" "MONORAIL_VOLUME.PRIMARY_S3"
)
SECONDARY_GCS_LOCATION_ID = (
    "SPRINGFIELD.NUCLEAR/external_volume_storage_location/"
    "MONORAIL_VOLUME.SECONDARY_GCS"
)


@patch.object(
    cartography.intel.snowflake.external_volumes,
    "get",
    return_value=SNOWFLAKE_EXTERNAL_VOLUMES,
)
def test_sync_snowflake_external_volumes(mock_get, neo4j_session):
    # Arrange: the bucket, the KMS key and the IAM role all belong to the aws and gcp
    # modules, so seed them the way a real graph would already have them.
    _ensure_local_neo4j_has_test_account(neo4j_session)
    neo4j_session.run(
        "MERGE (b:AWSS3Bucket{name: $s3}) SET b.lastupdated = $tag "
        "MERGE (g:GCPBucket{id: $gcs}) SET g.lastupdated = $tag "
        "MERGE (k:AWSKMSKey{arn: $kms}) SET k.lastupdated = $tag "
        "MERGE (p:AWSPrincipal{arn: $role}) SET p.lastupdated = $tag",
        s3=SNOWFLAKE_VOLUME_S3_BUCKET,
        gcs=SNOWFLAKE_VOLUME_GCS_BUCKET,
        kms=SNOWFLAKE_VOLUME_KMS_KEY_ARN,
        role=SNOWFLAKE_VOLUME_ROLE_ARN,
        tag=TEST_UPDATE_TAG,
    )

    # Act
    complete = cartography.intel.snowflake.external_volumes.sync(
        neo4j_session,
        build_test_client(),
        {"UPDATE_TAG": TEST_UPDATE_TAG, "ACCOUNT_ID": SNOWFLAKE_ACCOUNT_ID},
    )

    # Assert
    assert complete is True
    assert check_nodes(
        neo4j_session,
        "SnowflakeExternalVolume",
        ["id", "name", "allow_writes", "storage_location_count"],
    ) == {
        (MONORAIL_VOLUME_ID, "MONORAIL_VOLUME", True, 2),
        (DUFF_VOLUME_ID, "DUFF_VOLUME", False, 0),
    }
    # Each storage location is its own node, because it is the location and not the
    # volume that carries the bucket, the role and the encryption key.
    assert check_nodes(
        neo4j_session,
        "SnowflakeExternalVolumeStorageLocation",
        ["id", "name", "storage_provider", "encryption_type", "s3_bucket"],
    ) == {
        (
            PRIMARY_S3_LOCATION_ID,
            "PRIMARY_S3",
            "S3",
            "AWS_SSE_KMS",
            SNOWFLAKE_VOLUME_S3_BUCKET,
        ),
        (SECONDARY_GCS_LOCATION_ID, "SECONDARY_GCS", "GCS", "NONE", None),
    }
    assert check_nodes(neo4j_session, "ObjectStorage", ["id"]) >= {
        (PRIMARY_S3_LOCATION_ID,),
        (SECONDARY_GCS_LOCATION_ID,),
    }
    assert check_rels(
        neo4j_session,
        "SnowflakeExternalVolume",
        "id",
        "SnowflakeExternalVolumeStorageLocation",
        "id",
        "HAS_STORAGE_LOCATION",
        rel_direction_right=True,
    ) == {
        (MONORAIL_VOLUME_ID, PRIMARY_S3_LOCATION_ID),
        (MONORAIL_VOLUME_ID, SECONDARY_GCS_LOCATION_ID),
    }

    # The cross-cloud payoff: the Iceberg storage location is joined to the concrete
    # bucket, to the KMS key protecting it and to the IAM role Snowflake assumes.
    assert check_rels(
        neo4j_session,
        "SnowflakeExternalVolumeStorageLocation",
        "id",
        "AWSS3Bucket",
        "name",
        "BACKED_BY",
        rel_direction_right=True,
    ) == {(PRIMARY_S3_LOCATION_ID, SNOWFLAKE_VOLUME_S3_BUCKET)}
    assert check_rels(
        neo4j_session,
        "SnowflakeExternalVolumeStorageLocation",
        "id",
        "GCPBucket",
        "id",
        "BACKED_BY",
        rel_direction_right=True,
    ) == {(SECONDARY_GCS_LOCATION_ID, SNOWFLAKE_VOLUME_GCS_BUCKET)}
    assert check_rels(
        neo4j_session,
        "SnowflakeExternalVolumeStorageLocation",
        "id",
        "AWSKMSKey",
        "arn",
        "ENCRYPTED_BY",
        rel_direction_right=True,
    ) == {(PRIMARY_S3_LOCATION_ID, SNOWFLAKE_VOLUME_KMS_KEY_ARN)}
    assert check_rels(
        neo4j_session,
        "SnowflakeExternalVolumeStorageLocation",
        "id",
        "AWSPrincipal",
        "arn",
        "ASSUMES_ROLE",
        rel_direction_right=True,
    ) == {(PRIMARY_S3_LOCATION_ID, SNOWFLAKE_VOLUME_ROLE_ARN)}
