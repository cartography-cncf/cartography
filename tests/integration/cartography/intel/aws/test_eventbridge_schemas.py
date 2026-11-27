from unittest.mock import MagicMock
from unittest.mock import patch

from botocore.exceptions import ClientError

import cartography.intel.aws.eventbridge_schemas
from cartography.intel.aws.eventbridge_schemas import sync
from tests.data.aws.eventbridge_schemas import GET_EVENT_SCHEMA_REGISTRIES
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "123456789012"
TEST_REGION = "us-east-1"
TEST_UPDATE_TAG = 123456789
CUSTOM_REGISTRY_ARN = GET_EVENT_SCHEMA_REGISTRIES[0]["RegistryArn"]
OTHER_REGISTRY_ARN = GET_EVENT_SCHEMA_REGISTRIES[1]["RegistryArn"]


@patch.object(
    cartography.intel.aws.eventbridge_schemas,
    "get_event_schema_registries",
    return_value=GET_EVENT_SCHEMA_REGISTRIES,
)
def test_sync_eventbridge_schema_registries(mock_get_registries, neo4j_session):
    # Arrange
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    # Act
    sync(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Assert
    assert check_nodes(
        neo4j_session,
        "AWSEventSchemasRegistry",
        ["arn", "name", "region"],
    ) == {
        (CUSTOM_REGISTRY_ARN, "custom-registry", TEST_REGION),
        (OTHER_REGISTRY_ARN, "other-registry", TEST_REGION),
    }

    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "AWSEventSchemasRegistry",
        "arn",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (TEST_ACCOUNT_ID, CUSTOM_REGISTRY_ARN),
        (TEST_ACCOUNT_ID, OTHER_REGISTRY_ARN),
    }

    # Act and assert: a registry gone from AWS is cleaned up
    mock_get_registries.return_value = [GET_EVENT_SCHEMA_REGISTRIES[0]]
    sync(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG + 1,
        {"UPDATE_TAG": TEST_UPDATE_TAG + 1, "AWS_ID": TEST_ACCOUNT_ID},
    )

    assert check_nodes(neo4j_session, "AWSEventSchemasRegistry", ["arn"]) == {
        (CUSTOM_REGISTRY_ARN,),
    }


def test_sync_eventbridge_schema_registries_keeps_data_when_region_fails(
    neo4j_session,
):
    # Arrange
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
    with patch.object(
        cartography.intel.aws.eventbridge_schemas,
        "get_event_schema_registries",
        return_value=GET_EVENT_SCHEMA_REGISTRIES,
    ):
        sync(
            neo4j_session,
            MagicMock(),
            [TEST_REGION],
            TEST_ACCOUNT_ID,
            TEST_UPDATE_TAG,
            {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
        )

    boto3_session = MagicMock()
    paginator = boto3_session.client.return_value.get_paginator.return_value
    paginator.paginate.side_effect = ClientError(
        {
            "Error": {"Code": "InternalServerErrorException", "Message": ""},
            "ResponseMetadata": {"HTTPStatusCode": 500},
        },
        "ListRegistries",
    )

    # Act
    sync(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG + 1,
        {"UPDATE_TAG": TEST_UPDATE_TAG + 1, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Assert
    assert check_nodes(neo4j_session, "AWSEventSchemasRegistry", ["arn"]) == {
        (CUSTOM_REGISTRY_ARN,),
        (OTHER_REGISTRY_ARN,),
    }
