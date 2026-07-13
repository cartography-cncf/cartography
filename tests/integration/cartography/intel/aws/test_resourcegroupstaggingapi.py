import copy
from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.ec2.instances
import cartography.intel.aws.resourcegroupstaggingapi as rgta
from cartography.intel.aws.ec2.instances import sync_ec2_instances
from cartography.intel.aws.ec2.load_balancers import load_load_balancers
from cartography.intel.aws.resourcegroupstaggingapi import sync
from tests.data.aws.ec2.instances import DESCRIBE_INSTANCES
from tests.data.aws.resourcegroupstaggingapi import GET_RESOURCES_RESPONSE
from tests.data.aws.resourcegroupstaggingapi import GET_RESOURCES_RESPONSE_LB_US_EAST_1
from tests.data.aws.resourcegroupstaggingapi import GET_RESOURCES_RESPONSE_LB_US_WEST_2
from tests.data.aws.resourcegroupstaggingapi import LOAD_BALANCERS_US_EAST_1
from tests.data.aws.resourcegroupstaggingapi import LOAD_BALANCERS_US_WEST_2
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
    return_value=copy.deepcopy(GET_RESOURCES_RESPONSE),
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

    # Assert - AWSTag nodes exist and carry the ontology _ont_source.
    assert check_nodes(
        neo4j_session, "AWSTag", ["id", "key", "value", "_ont_source"]
    ) == {
        ("TestKey:TestValue", "TestKey", "TestValue", "aws"),
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

    # Assert - AWSTag nodes no longer carry a region property (#1094). The
    # property is meaningless on a shared Key:Value node and has been dropped.
    region_props = neo4j_session.run(
        "MATCH (n:AWSTag) RETURN keys(n) AS props",
    ).single()["props"]
    assert "region" not in region_props


def test_sync_tags_scopes_to_correct_region(neo4j_session):
    """
    Regression test for #1137: two load balancers with the same name in two
    different regions must each be tagged with only their own region's tags.
    The classic LB tag mapping is keyed by the non-unique `name`, so before the
    region predicate both LBs were cross-tagged.
    """
    # Arrange - account plus two same-named LBs in two regions
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
    load_load_balancers(
        neo4j_session,
        LOAD_BALANCERS_US_EAST_1,
        "us-east-1",
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )
    load_load_balancers(
        neo4j_session,
        LOAD_BALANCERS_US_WEST_2,
        "us-west-2",
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    # Act - sync tags for both regions; each region returns its own tag data
    tag_data_by_region = {
        "us-east-1": GET_RESOURCES_RESPONSE_LB_US_EAST_1,
        "us-west-2": GET_RESOURCES_RESPONSE_LB_US_WEST_2,
    }

    def fake_get_tags(_boto3_session, _resource_types, region):
        return copy.deepcopy(tag_data_by_region[region])

    test_mapping = {
        "elasticloadbalancing:loadbalancer": rgta.TAG_RESOURCE_TYPE_MAPPINGS[
            "elasticloadbalancing:loadbalancer"
        ],
    }
    with patch.object(rgta, "get_tags", side_effect=fake_get_tags):
        sync(
            neo4j_session,
            boto3_session,
            ["us-east-1", "us-west-2"],
            TEST_ACCOUNT_ID,
            TEST_UPDATE_TAG,
            {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
            tag_resource_type_mappings=test_mapping,
        )

    # Assert - each LB is tagged only with its own region's tag, identified by
    # the region-specific `id`.
    assert check_rels(
        neo4j_session,
        "LoadBalancer",
        "id",
        "AWSTag",
        "id",
        "TAGGED",
        rel_direction_right=True,
    ) == {
        (LOAD_BALANCERS_US_EAST_1[0]["id"], "env:prod"),
        (LOAD_BALANCERS_US_WEST_2[0]["id"], "env:staging"),
    }
