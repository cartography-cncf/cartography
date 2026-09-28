from unittest.mock import patch

import cartography.intel.snowflake.storage_integrations
from tests.data.snowflake.account import SNOWFLAKE_ACCOUNT_ID
from tests.data.snowflake.storage_integrations import (
    SNOWFLAKE_STORAGE_INTEGRATION_DETAILS,
)
from tests.data.snowflake.storage_integrations import (
    SNOWFLAKE_STORAGE_INTEGRATION_ROLE_ARN,
)
from tests.data.snowflake.storage_integrations import SNOWFLAKE_STORAGE_INTEGRATIONS
from tests.integration.cartography.intel.snowflake.test_account import (
    _ensure_local_neo4j_has_test_account,
)
from tests.integration.cartography.intel.snowflake.test_account import build_test_client
from tests.integration.cartography.intel.snowflake.test_account import TEST_UPDATE_TAG
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

PLANT_S3_INTEGRATION_ID = "SPRINGFIELD.NUCLEAR/storage_integration/PLANT_S3_INTEGRATION"
SQUISHEE_AZURE_INTEGRATION_ID = (
    "SPRINGFIELD.NUCLEAR/storage_integration/SQUISHEE_AZURE_INTEGRATION"
)


def _details_for(client, name):
    return SNOWFLAKE_STORAGE_INTEGRATION_DETAILS[name]


def _ensure_local_neo4j_has_test_storage_integrations(neo4j_session) -> None:
    """Seed the storage integrations a stage's USES_INTEGRATION edge resolves against."""
    _ensure_local_neo4j_has_test_account(neo4j_session)
    cartography.intel.snowflake.storage_integrations.load_storage_integrations(
        neo4j_session,
        cartography.intel.snowflake.storage_integrations.transform(
            SNOWFLAKE_STORAGE_INTEGRATIONS,
            SNOWFLAKE_STORAGE_INTEGRATION_DETAILS,
            SNOWFLAKE_ACCOUNT_ID,
        ),
        SNOWFLAKE_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.snowflake.storage_integrations,
    "get_details",
    side_effect=_details_for,
)
@patch.object(
    cartography.intel.snowflake.storage_integrations,
    "get",
    return_value=SNOWFLAKE_STORAGE_INTEGRATIONS,
)
def test_sync_snowflake_storage_integrations(mock_get, mock_details, neo4j_session):
    # Arrange: the IAM role Snowflake assumes belongs to the aws module, so seed the
    # principal the ASSUMES_ROLE edge has to resolve against.
    _ensure_local_neo4j_has_test_account(neo4j_session)
    neo4j_session.run(
        "MERGE (p:AWSPrincipal{arn: $arn}) SET p.lastupdated = $tag",
        arn=SNOWFLAKE_STORAGE_INTEGRATION_ROLE_ARN,
        tag=TEST_UPDATE_TAG,
    )

    # Act
    complete = cartography.intel.snowflake.storage_integrations.sync(
        neo4j_session,
        build_test_client(),
        {"UPDATE_TAG": TEST_UPDATE_TAG, "ACCOUNT_ID": SNOWFLAKE_ACCOUNT_ID},
    )

    # Assert: the SQL API's "true"/"false" strings become booleans, and DESC-only
    # fields such as the external id land on the node.
    assert complete is True
    assert check_nodes(
        neo4j_session,
        "SnowflakeStorageIntegration",
        [
            "id",
            "name",
            "enabled",
            "storage_provider",
            "storage_aws_external_id",
            "use_privatelink_endpoint",
        ],
    ) == {
        (
            PLANT_S3_INTEGRATION_ID,
            "PLANT_S3_INTEGRATION",
            True,
            "S3",
            "SPRINGFIELD_NUCLEAR_SFCRole=5_stuvwx==",
            False,
        ),
        (
            SQUISHEE_AZURE_INTEGRATION_ID,
            "SQUISHEE_AZURE_INTEGRATION",
            False,
            "AZURE",
            None,
            True,
        ),
    }
    assert check_rels(
        neo4j_session,
        "SnowflakeStorageIntegration",
        "id",
        "SnowflakeAccount",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        (PLANT_S3_INTEGRATION_ID, SNOWFLAKE_ACCOUNT_ID),
        (SQUISHEE_AZURE_INTEGRATION_ID, SNOWFLAKE_ACCOUNT_ID),
    }
    # The cross-cloud payoff: the Snowflake integration is joined to the concrete AWS
    # IAM role it assumes, so an attack path can cross from Snowflake into AWS.
    assert check_rels(
        neo4j_session,
        "SnowflakeStorageIntegration",
        "id",
        "AWSPrincipal",
        "arn",
        "ASSUMES_ROLE",
        rel_direction_right=True,
    ) == {(PLANT_S3_INTEGRATION_ID, SNOWFLAKE_STORAGE_INTEGRATION_ROLE_ARN)}


def test_sync_snowflake_storage_integrations_undescribable(neo4j_session):
    # Arrange: a previous run collected both integrations in full, then SHOW succeeds
    # but DESC is not permitted for any of them. Seeding explicitly rather than relying
    # on the preceding test's leftover graph keeps this runnable on its own.
    _ensure_local_neo4j_has_test_storage_integrations(neo4j_session)

    # Act
    with (
        patch.object(
            cartography.intel.snowflake.storage_integrations,
            "get",
            return_value=SNOWFLAKE_STORAGE_INTEGRATIONS,
        ),
        patch.object(
            cartography.intel.snowflake.storage_integrations,
            "get_details",
            return_value=None,
        ),
    ):
        complete = cartography.intel.snowflake.storage_integrations.sync(
            neo4j_session,
            build_test_client(),
            {"UPDATE_TAG": TEST_UPDATE_TAG, "ACCOUNT_ID": SNOWFLAKE_ACCOUNT_ID},
        )

    # Assert: the sync reports itself incomplete so cleanup does not run on half-read
    # data, and the integrations keep the values the earlier run collected.
    #
    # This is the point of the fix. An integration listed by SHOW but not describable
    # has none of its interesting properties, so loading it anyway would write null
    # over the IAM role ARN, the allowed locations and the external id an earlier run
    # had. Skipping cleanup does not protect them, because load() still rewrites
    # whatever node it is handed.
    assert complete is False
    assert check_nodes(
        neo4j_session,
        "SnowflakeStorageIntegration",
        ["id", "storage_provider"],
    ) == {
        (PLANT_S3_INTEGRATION_ID, "S3"),
        (SQUISHEE_AZURE_INTEGRATION_ID, "AZURE"),
    }
