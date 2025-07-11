from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.ec2
import tests.data.aws.ec2.security_groups
import tests.data.aws.ec2.security_group_rules
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "000000000000"
TEST_REGION = "eu-north-1"
TEST_UPDATE_TAG = 123456789


@patch.object(
    cartography.intel.aws.ec2.security_groups,
    "get_ec2_security_group_rules",
    return_value=tests.data.aws.ec2.security_group_rules.DESCRIBE_SECURITY_GROUP_RULES,
)
def test_load_security_groups(mock_get_rules, neo4j_session):
    # Arrange
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
    data = tests.data.aws.ec2.security_groups.DESCRIBE_SGS
    cartography.intel.aws.ec2.security_groups.load_ec2_security_groupinfo(
        neo4j_session,
        boto3_session,
        data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    # Assert
    assert check_nodes(neo4j_session, "EC2SecurityGroup", ["id"]) == {
        ("sg-0fd4fff275d63600f",),
        ("sg-028e2522c72719996",),
        ("sg-06c795c66be8937be",),
        ("sg-053dba35430032a0d",),
    }


@patch.object(
    cartography.intel.aws.ec2.security_groups,
    "get_ec2_security_group_rules",
    return_value=tests.data.aws.ec2.security_group_rules.DESCRIBE_SECURITY_GROUP_RULES,
)
def test_load_security_groups_relationships(mock_get_rules, neo4j_session):
    # Arrange
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    data = tests.data.aws.ec2.security_groups.DESCRIBE_SGS
    cartography.intel.aws.ec2.security_groups.load_ec2_security_groupinfo(
        neo4j_session,
        boto3_session,
        data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    # Assert
    # Get all relationships
    rels = check_rels(
        neo4j_session,
        "EC2SecurityGroup",
        "id",
        "IpRule",
        "ruleid",
        "MEMBER_OF_EC2_SECURITY_GROUP",
        rel_direction_right=False,
    )

    # Filter only relationships for sg-028e2522c72719996
    sg_rels = {rel for rel in rels if rel[0] == "sg-028e2522c72719996"}

    # Assert that we have all expected relationships
    assert sg_rels == {
        ("sg-028e2522c72719996", "sgr-01234567890abcdef"),
        ("sg-028e2522c72719996", "sgr-abcdef01234567890"),
        ("sg-028e2522c72719996", "sgr-11111111111111111"),
        ("sg-028e2522c72719996", "sgr-22222222222222222"),
        ("sg-028e2522c72719996", "sgr-33333333333333333"),
    }


@patch.object(
    cartography.intel.aws.ec2.security_groups,
    "get_ec2_security_group_rules",
    return_value=tests.data.aws.ec2.security_group_rules.DESCRIBE_SECURITY_GROUP_RULES,
)
def test_security_group_rules(mock_get_rules, neo4j_session):
    # Arrange
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    data = tests.data.aws.ec2.security_groups.DESCRIBE_SGS
    cartography.intel.aws.ec2.security_groups.load_ec2_security_groupinfo(
        neo4j_session,
        boto3_session,
        data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    # Assert
    assert check_nodes(neo4j_session, "IpRule", ["ruleid"]) == {
        ("sgr-01234567890abcdef",),
        ("sgr-abcdef01234567890",),
        ("sgr-11111111111111111",),
        ("sgr-22222222222222222",),
        ("sgr-33333333333333333",),
    }

    # Verify rule properties
    result = neo4j_session.run("""
        MATCH (r:IpRule)
        WHERE r.ruleid = $rule_id
        RETURN r.fromport, r.toport, r.protocol
    """, rule_id="sgr-01234567890abcdef")

    rule = result.single()
    assert rule["r.fromport"] == 80
    assert rule["r.toport"] == 80
    assert rule["r.protocol"] == "tcp"

    # Verify IP ranges
    result = neo4j_session.run("""
        MATCH (r:IpRule)<-[:MEMBER_OF_IP_RULE]-(range:IpRange)
        WHERE r.ruleid = $rule_id
        RETURN range.range
    """, rule_id="sgr-01234567890abcdef")

    range_data = result.single()
    assert range_data["range.range"] == "203.0.113.0/24"
