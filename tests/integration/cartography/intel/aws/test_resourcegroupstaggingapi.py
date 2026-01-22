from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.ec2.instances
import cartography.intel.aws.resourcegroupstaggingapi as rgta
from cartography.intel.aws.ec2.instances import sync_ec2_instances
from cartography.intel.aws.resourcegroupstaggingapi import sync
from tests.data.aws.ec2.instances import DESCRIBE_INSTANCES
from tests.data.aws.resourcegroupstaggingapi import GET_RESOURCES_RESPONSE
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "1234"
TEST_REGION = "us-east-1"
TEST_UPDATE_TAG = 123456789


@patch.object(
    cartography.intel.aws.ec2.instances,
    "get_ec2_instances",
    return_value=DESCRIBE_INSTANCES["Reservations"],
)
@patch.object(
    rgta,
    "get_tags",
    return_value=GET_RESOURCES_RESPONSE,
)
def test_sync_tags(mock_get_tags, mock_get_instances, neo4j_session):
    """
    Verify that sync() creates AWSTag nodes and (Resource)-[:TAGGED]->(AWSTag) relationships.
    """
    # Arrange
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    # First sync EC2 instances so we have resources to tag
    sync_ec2_instances(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Act - sync tags using the sync() function
    # Use a limited mapping to only test ec2:instance tags
    test_mapping = {
        "ec2:instance": rgta.TAG_RESOURCE_TYPE_MAPPINGS["ec2:instance"],
    }
    sync(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
        tag_resource_type_mappings=test_mapping,
    )

    # Assert - AWSTag nodes exist
    assert check_nodes(neo4j_session, "AWSTag", ["id", "key", "value"]) == {
        ("TestKey:TestValue", "TestKey", "TestValue"),
    }

    # Assert - Relationships (EC2Instance)-[TAGGED]->(AWSTag)
    assert check_rels(
        neo4j_session,
        "EC2Instance",
        "id",
        "AWSTag",
        "id",
        "TAGGED",
        rel_direction_right=True,
    ) == {
        ("i-01", "TestKey:TestValue"),
    }
