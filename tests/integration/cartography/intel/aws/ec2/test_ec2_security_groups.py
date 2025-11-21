from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.ec2
import cartography.intel.aws.ec2.security_groups
import tests.data.aws.ec2.security_groups
from tests.data.aws.ec2.security_groups import DESCRIBE_SGS
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "000000000000"
TEST_REGION = "eu-north-1"
TEST_UPDATE_TAG = 123456789


def test_load_security_groups(neo4j_session):
    data = tests.data.aws.ec2.security_groups.DESCRIBE_SGS
    transformed = (
        cartography.intel.aws.ec2.security_groups.transform_ec2_security_group_data(
            data
        )
    )
    cartography.intel.aws.ec2.security_groups.load_ec2_security_groupinfo(
        neo4j_session,
        transformed,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "sg-0fd4fff275d63600f",
        "sg-028e2522c72719996",
        "sg-06c795c66be8937be",
        "sg-053dba35430032a0d",
        "sg-web-server-12345",
    }

    nodes = neo4j_session.run(
        """
        MATCH (s:EC2SecurityGroup) RETURN s.id;
        """,
    )
    actual_nodes = {n["s.id"] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_security_groups_relationships(neo4j_session):
    # Create Test AWSAccount
    neo4j_session.run(
        """
        MERGE (aws:AWSAccount{id: $aws_account_id})
        ON CREATE SET aws.firstseen = timestamp()
        SET aws.lastupdated = $aws_update_tag
        """,
        aws_account_id=TEST_ACCOUNT_ID,
        aws_update_tag=TEST_UPDATE_TAG,
    )

    data = tests.data.aws.ec2.security_groups.DESCRIBE_SGS
    transformed = (
        cartography.intel.aws.ec2.security_groups.transform_ec2_security_group_data(
            data
        )
    )
    cartography.intel.aws.ec2.security_groups.load_ec2_security_groupinfo(
        neo4j_session,
        transformed,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        ("sg-028e2522c72719996", "sg-028e2522c72719996/IpPermissionsEgress/443443tcp"),
        ("sg-028e2522c72719996", "sg-028e2522c72719996/IpPermissionsEgress/NoneNone-1"),
        ("sg-028e2522c72719996", "sg-028e2522c72719996/IpPermissionsEgress/8080tcp"),
        ("sg-028e2522c72719996", "sg-028e2522c72719996/IpPermissions/443443tcp"),
        ("sg-028e2522c72719996", "sg-028e2522c72719996/IpPermissions/8080tcp"),
        ("sg-053dba35430032a0d", "sg-053dba35430032a0d/IpPermissionsEgress/NoneNone-1"),
        ("sg-053dba35430032a0d", "sg-053dba35430032a0d/IpPermissions/NoneNone-1"),
        ("sg-06c795c66be8937be", "sg-06c795c66be8937be/IpPermissionsEgress/443443tcp"),
        ("sg-06c795c66be8937be", "sg-06c795c66be8937be/IpPermissionsEgress/NoneNone-1"),
        ("sg-06c795c66be8937be", "sg-06c795c66be8937be/IpPermissionsEgress/8080tcp"),
        ("sg-06c795c66be8937be", "sg-06c795c66be8937be/IpPermissions/443443tcp"),
        ("sg-06c795c66be8937be", "sg-06c795c66be8937be/IpPermissions/8080tcp"),
        ("sg-0fd4fff275d63600f", "sg-0fd4fff275d63600f/IpPermissionsEgress/NoneNone-1"),
        ("sg-0fd4fff275d63600f", "sg-0fd4fff275d63600f/IpPermissions/NoneNone-1"),
        ("sg-web-server-12345", "sg-web-server-12345/IpPermissionsEgress/NoneNone-1"),
        ("sg-web-server-12345", "sg-web-server-12345/IpPermissions/2222tcp"),
        ("sg-web-server-12345", "sg-web-server-12345/IpPermissions/8080tcp"),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (s:EC2SecurityGroup)-[]-(r:IpRule) RETURN s.id,r.ruleid;
        """,
    )
    actual = {(r["s.id"], r["r.ruleid"]) for r in result}

    assert actual == expected_nodes


@patch.object(
    cartography.intel.aws.ec2.security_groups,
    "get_ec2_security_group_data",
    return_value=DESCRIBE_SGS,
)
def test_sync_ec2_security_groupinfo(mock_get_security_groups, neo4j_session):
    """
    Test that EC2 security groups sync correctly and create proper nodes and relationships
    """
    # Arrange
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    # Act
    cartography.intel.aws.ec2.security_groups.sync_ec2_security_groupinfo(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Assert EC2 security groups exist
    assert check_nodes(neo4j_session, "EC2SecurityGroup", ["id", "groupid"]) == {
        ("sg-028e2522c72719996", "sg-028e2522c72719996"),
        ("sg-053dba35430032a0d", "sg-053dba35430032a0d"),
        ("sg-06c795c66be8937be", "sg-06c795c66be8937be"),
        ("sg-0fd4fff275d63600f", "sg-0fd4fff275d63600f"),
        ("sg-web-server-12345", "sg-web-server-12345"),
    }

    # Assert security groups are connected to AWS account
    assert check_rels(
        neo4j_session,
        "EC2SecurityGroup",
        "id",
        "AWSAccount",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        ("sg-028e2522c72719996", "000000000000"),
        ("sg-053dba35430032a0d", "000000000000"),
        ("sg-06c795c66be8937be", "000000000000"),
        ("sg-0fd4fff275d63600f", "000000000000"),
        ("sg-web-server-12345", "000000000000"),
    }

    # Assert IpPermissionInbound rules exist (only inbound rules)
    expected_inbound_rules = {
        ("sg-028e2522c72719996/IpPermissions/8080tcp", "sg-028e2522c72719996"),
        ("sg-028e2522c72719996/IpPermissions/443443tcp", "sg-028e2522c72719996"),
        ("sg-053dba35430032a0d/IpPermissions/NoneNone-1", "sg-053dba35430032a0d"),
        ("sg-06c795c66be8937be/IpPermissions/8080tcp", "sg-06c795c66be8937be"),
        ("sg-06c795c66be8937be/IpPermissions/443443tcp", "sg-06c795c66be8937be"),
        ("sg-0fd4fff275d63600f/IpPermissions/NoneNone-1", "sg-0fd4fff275d63600f"),
        ("sg-web-server-12345/IpPermissions/2222tcp", "sg-web-server-12345"),
        ("sg-web-server-12345/IpPermissions/8080tcp", "sg-web-server-12345"),
    }
    assert (
        check_nodes(neo4j_session, "IpPermissionInbound", ["ruleid", "groupid"])
        == expected_inbound_rules
    )

    # Assert IpRule rules exist (both inbound and outbound rules mixed together)
    expected_ip_rules = {
        ("sg-028e2522c72719996/IpPermissionsEgress/8080tcp", "sg-028e2522c72719996"),
        ("sg-028e2522c72719996/IpPermissionsEgress/443443tcp", "sg-028e2522c72719996"),
        ("sg-028e2522c72719996/IpPermissionsEgress/NoneNone-1", "sg-028e2522c72719996"),
        ("sg-028e2522c72719996/IpPermissions/8080tcp", "sg-028e2522c72719996"),
        ("sg-028e2522c72719996/IpPermissions/443443tcp", "sg-028e2522c72719996"),
        ("sg-053dba35430032a0d/IpPermissionsEgress/NoneNone-1", "sg-053dba35430032a0d"),
        ("sg-053dba35430032a0d/IpPermissions/NoneNone-1", "sg-053dba35430032a0d"),
        ("sg-06c795c66be8937be/IpPermissionsEgress/8080tcp", "sg-06c795c66be8937be"),
        ("sg-06c795c66be8937be/IpPermissionsEgress/443443tcp", "sg-06c795c66be8937be"),
        ("sg-06c795c66be8937be/IpPermissionsEgress/NoneNone-1", "sg-06c795c66be8937be"),
        ("sg-06c795c66be8937be/IpPermissions/8080tcp", "sg-06c795c66be8937be"),
        ("sg-06c795c66be8937be/IpPermissions/443443tcp", "sg-06c795c66be8937be"),
        ("sg-0fd4fff275d63600f/IpPermissionsEgress/NoneNone-1", "sg-0fd4fff275d63600f"),
        ("sg-0fd4fff275d63600f/IpPermissions/NoneNone-1", "sg-0fd4fff275d63600f"),
        ("sg-web-server-12345/IpPermissionsEgress/NoneNone-1", "sg-web-server-12345"),
        ("sg-web-server-12345/IpPermissions/2222tcp", "sg-web-server-12345"),
        ("sg-web-server-12345/IpPermissions/8080tcp", "sg-web-server-12345"),
    }
    assert (
        check_nodes(neo4j_session, "IpRule", ["ruleid", "groupid"]) == expected_ip_rules
    )

    # Assert IpRule rules are connected to AWS account
    assert check_rels(
        neo4j_session,
        "IpRule",
        "ruleid",
        "AWSAccount",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        ("sg-028e2522c72719996/IpPermissionsEgress/8080tcp", "000000000000"),
        ("sg-028e2522c72719996/IpPermissionsEgress/443443tcp", "000000000000"),
        ("sg-028e2522c72719996/IpPermissionsEgress/NoneNone-1", "000000000000"),
        ("sg-028e2522c72719996/IpPermissions/8080tcp", "000000000000"),
        ("sg-028e2522c72719996/IpPermissions/443443tcp", "000000000000"),
        ("sg-053dba35430032a0d/IpPermissionsEgress/NoneNone-1", "000000000000"),
        ("sg-053dba35430032a0d/IpPermissions/NoneNone-1", "000000000000"),
        ("sg-06c795c66be8937be/IpPermissionsEgress/8080tcp", "000000000000"),
        ("sg-06c795c66be8937be/IpPermissionsEgress/443443tcp", "000000000000"),
        ("sg-06c795c66be8937be/IpPermissionsEgress/NoneNone-1", "000000000000"),
        ("sg-06c795c66be8937be/IpPermissions/8080tcp", "000000000000"),
        ("sg-06c795c66be8937be/IpPermissions/443443tcp", "000000000000"),
        ("sg-0fd4fff275d63600f/IpPermissionsEgress/NoneNone-1", "000000000000"),
        ("sg-0fd4fff275d63600f/IpPermissions/NoneNone-1", "000000000000"),
        ("sg-web-server-12345/IpPermissionsEgress/NoneNone-1", "000000000000"),
        ("sg-web-server-12345/IpPermissions/2222tcp", "000000000000"),
        ("sg-web-server-12345/IpPermissions/8080tcp", "000000000000"),
    }

    assert check_rels(
        neo4j_session,
        "EC2SecurityGroup",
        "id",
        "EC2SecurityGroup",
        "id",
        "ALLOWS_TRAFFIC_FROM",
        rel_direction_right=True,
    ) == {
        # Test self-referential security groups
        ("sg-053dba35430032a0d", "sg-053dba35430032a0d"),
        ("sg-0fd4fff275d63600f", "sg-0fd4fff275d63600f"),
        # Test cross-security group relationships
        ("sg-web-server-12345", "sg-028e2522c72719996"),
    }
