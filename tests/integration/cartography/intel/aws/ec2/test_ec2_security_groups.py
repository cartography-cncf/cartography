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
        MATCH (s:AWSEC2SecurityGroup) RETURN s.id;
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
        SET aws.lastupdated = $aws_update_tag, aws :Tenant
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
        (
            "sg-028e2522c72719996",
            "sg-028e2522c72719996/IpPermissionsEgress/443/443/tcp",
        ),
        (
            "sg-028e2522c72719996",
            "sg-028e2522c72719996/IpPermissionsEgress/None/None/-1",
        ),
        ("sg-028e2522c72719996", "sg-028e2522c72719996/IpPermissionsEgress/80/80/tcp"),
        ("sg-028e2522c72719996", "sg-028e2522c72719996/IpPermissions/443/443/tcp"),
        ("sg-028e2522c72719996", "sg-028e2522c72719996/IpPermissions/80/80/tcp"),
        (
            "sg-053dba35430032a0d",
            "sg-053dba35430032a0d/IpPermissionsEgress/None/None/-1",
        ),
        ("sg-053dba35430032a0d", "sg-053dba35430032a0d/IpPermissions/None/None/-1"),
        (
            "sg-06c795c66be8937be",
            "sg-06c795c66be8937be/IpPermissionsEgress/443/443/tcp",
        ),
        (
            "sg-06c795c66be8937be",
            "sg-06c795c66be8937be/IpPermissionsEgress/None/None/-1",
        ),
        ("sg-06c795c66be8937be", "sg-06c795c66be8937be/IpPermissionsEgress/80/80/tcp"),
        ("sg-06c795c66be8937be", "sg-06c795c66be8937be/IpPermissions/443/443/tcp"),
        ("sg-06c795c66be8937be", "sg-06c795c66be8937be/IpPermissions/80/80/tcp"),
        (
            "sg-0fd4fff275d63600f",
            "sg-0fd4fff275d63600f/IpPermissionsEgress/None/None/-1",
        ),
        ("sg-0fd4fff275d63600f", "sg-0fd4fff275d63600f/IpPermissions/None/None/-1"),
        ("sg-web-server-12345", "sg-web-server-12345/IpPermissionsEgress/None/None/-1"),
        ("sg-web-server-12345", "sg-web-server-12345/IpPermissions/22/22/tcp"),
        ("sg-web-server-12345", "sg-web-server-12345/IpPermissions/22/2222/tcp"),
        ("sg-web-server-12345", "sg-web-server-12345/IpPermissions/80/80/tcp"),
        ("sg-web-server-12345", "sg-web-server-12345/IpPermissions/222/222/tcp"),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (s:AWSEC2SecurityGroup)-[]-(r:IpRule) RETURN s.id,r.ruleid;
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
    assert check_nodes(neo4j_session, "AWSEC2SecurityGroup", ["id", "groupid"]) == {
        ("sg-028e2522c72719996", "sg-028e2522c72719996"),
        ("sg-053dba35430032a0d", "sg-053dba35430032a0d"),
        ("sg-06c795c66be8937be", "sg-06c795c66be8937be"),
        ("sg-0fd4fff275d63600f", "sg-0fd4fff275d63600f"),
        ("sg-web-server-12345", "sg-web-server-12345"),
    }

    # Assert security groups are connected to AWS account
    assert check_rels(
        neo4j_session,
        "AWSEC2SecurityGroup",
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
        ("sg-028e2522c72719996/IpPermissions/80/80/tcp", "sg-028e2522c72719996"),
        ("sg-028e2522c72719996/IpPermissions/443/443/tcp", "sg-028e2522c72719996"),
        ("sg-053dba35430032a0d/IpPermissions/None/None/-1", "sg-053dba35430032a0d"),
        ("sg-06c795c66be8937be/IpPermissions/80/80/tcp", "sg-06c795c66be8937be"),
        ("sg-06c795c66be8937be/IpPermissions/443/443/tcp", "sg-06c795c66be8937be"),
        ("sg-0fd4fff275d63600f/IpPermissions/None/None/-1", "sg-0fd4fff275d63600f"),
        ("sg-web-server-12345/IpPermissions/22/22/tcp", "sg-web-server-12345"),
        ("sg-web-server-12345/IpPermissions/22/2222/tcp", "sg-web-server-12345"),
        ("sg-web-server-12345/IpPermissions/80/80/tcp", "sg-web-server-12345"),
        ("sg-web-server-12345/IpPermissions/222/222/tcp", "sg-web-server-12345"),
    }
    assert (
        check_nodes(neo4j_session, "IpPermissionInbound", ["ruleid", "groupid"])
        == expected_inbound_rules
    )

    # Assert each inbound rule keeps its own port range. sg-web-server-12345 holds
    # two rules whose ports and protocol concatenate to the same digits.
    assert check_nodes(
        neo4j_session, "IpPermissionInbound", ["groupid", "fromport", "toport"]
    ) == {
        ("sg-028e2522c72719996", 80, 80),
        ("sg-028e2522c72719996", 443, 443),
        ("sg-053dba35430032a0d", None, None),
        ("sg-06c795c66be8937be", 80, 80),
        ("sg-06c795c66be8937be", 443, 443),
        ("sg-0fd4fff275d63600f", None, None),
        ("sg-web-server-12345", 22, 22),
        ("sg-web-server-12345", 22, 2222),
        ("sg-web-server-12345", 80, 80),
        ("sg-web-server-12345", 222, 222),
    }

    # Assert IpRule rules exist (both inbound and outbound rules mixed together)
    expected_ip_rules = {
        ("sg-028e2522c72719996/IpPermissionsEgress/80/80/tcp", "sg-028e2522c72719996"),
        (
            "sg-028e2522c72719996/IpPermissionsEgress/443/443/tcp",
            "sg-028e2522c72719996",
        ),
        (
            "sg-028e2522c72719996/IpPermissionsEgress/None/None/-1",
            "sg-028e2522c72719996",
        ),
        ("sg-028e2522c72719996/IpPermissions/80/80/tcp", "sg-028e2522c72719996"),
        ("sg-028e2522c72719996/IpPermissions/443/443/tcp", "sg-028e2522c72719996"),
        (
            "sg-053dba35430032a0d/IpPermissionsEgress/None/None/-1",
            "sg-053dba35430032a0d",
        ),
        ("sg-053dba35430032a0d/IpPermissions/None/None/-1", "sg-053dba35430032a0d"),
        ("sg-06c795c66be8937be/IpPermissionsEgress/80/80/tcp", "sg-06c795c66be8937be"),
        (
            "sg-06c795c66be8937be/IpPermissionsEgress/443/443/tcp",
            "sg-06c795c66be8937be",
        ),
        (
            "sg-06c795c66be8937be/IpPermissionsEgress/None/None/-1",
            "sg-06c795c66be8937be",
        ),
        ("sg-06c795c66be8937be/IpPermissions/80/80/tcp", "sg-06c795c66be8937be"),
        ("sg-06c795c66be8937be/IpPermissions/443/443/tcp", "sg-06c795c66be8937be"),
        (
            "sg-0fd4fff275d63600f/IpPermissionsEgress/None/None/-1",
            "sg-0fd4fff275d63600f",
        ),
        ("sg-0fd4fff275d63600f/IpPermissions/None/None/-1", "sg-0fd4fff275d63600f"),
        ("sg-web-server-12345/IpPermissionsEgress/None/None/-1", "sg-web-server-12345"),
        ("sg-web-server-12345/IpPermissions/22/22/tcp", "sg-web-server-12345"),
        ("sg-web-server-12345/IpPermissions/22/2222/tcp", "sg-web-server-12345"),
        ("sg-web-server-12345/IpPermissions/80/80/tcp", "sg-web-server-12345"),
        ("sg-web-server-12345/IpPermissions/222/222/tcp", "sg-web-server-12345"),
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
        ("sg-028e2522c72719996/IpPermissionsEgress/80/80/tcp", "000000000000"),
        ("sg-028e2522c72719996/IpPermissionsEgress/443/443/tcp", "000000000000"),
        ("sg-028e2522c72719996/IpPermissionsEgress/None/None/-1", "000000000000"),
        ("sg-028e2522c72719996/IpPermissions/80/80/tcp", "000000000000"),
        ("sg-028e2522c72719996/IpPermissions/443/443/tcp", "000000000000"),
        ("sg-053dba35430032a0d/IpPermissionsEgress/None/None/-1", "000000000000"),
        ("sg-053dba35430032a0d/IpPermissions/None/None/-1", "000000000000"),
        ("sg-06c795c66be8937be/IpPermissionsEgress/80/80/tcp", "000000000000"),
        ("sg-06c795c66be8937be/IpPermissionsEgress/443/443/tcp", "000000000000"),
        ("sg-06c795c66be8937be/IpPermissionsEgress/None/None/-1", "000000000000"),
        ("sg-06c795c66be8937be/IpPermissions/80/80/tcp", "000000000000"),
        ("sg-06c795c66be8937be/IpPermissions/443/443/tcp", "000000000000"),
        ("sg-0fd4fff275d63600f/IpPermissionsEgress/None/None/-1", "000000000000"),
        ("sg-0fd4fff275d63600f/IpPermissions/None/None/-1", "000000000000"),
        ("sg-web-server-12345/IpPermissionsEgress/None/None/-1", "000000000000"),
        ("sg-web-server-12345/IpPermissions/22/22/tcp", "000000000000"),
        ("sg-web-server-12345/IpPermissions/22/2222/tcp", "000000000000"),
        ("sg-web-server-12345/IpPermissions/80/80/tcp", "000000000000"),
        ("sg-web-server-12345/IpPermissions/222/222/tcp", "000000000000"),
    }

    assert check_rels(
        neo4j_session,
        "AWSEC2SecurityGroup",
        "id",
        "AWSEC2SecurityGroup",
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


ACCOUNT_A = "111111111111"
ACCOUNT_B = "222222222222"
SHARED_CIDR = "10.215.0.0/16"


def _sg_with_cidrs(group_id: str, owner_id: str, cidrs: list[str]) -> dict:
    """A minimal security group with an inbound and an egress TCP/443 rule on `cidrs`."""
    rule = {
        "IpProtocol": "tcp",
        "FromPort": 443,
        "ToPort": 443,
        "IpRanges": [{"CidrIp": cidr} for cidr in cidrs],
        "Ipv6Ranges": [],
        "PrefixListIds": [],
        "UserIdGroupPairs": [],
    }
    return {
        "GroupId": group_id,
        "GroupName": group_id,
        "Description": group_id,
        "OwnerId": owner_id,
        "VpcId": f"vpc-{owner_id}",
        "IpPermissions": [rule],
        "IpPermissionsEgress": [rule],
    }


def _sync_account(neo4j_session, account_id: str, groups: list, update_tag: int):
    create_test_account(neo4j_session, account_id, update_tag)
    with patch.object(
        cartography.intel.aws.ec2.security_groups,
        "get_ec2_security_group_data",
        return_value=groups,
    ):
        cartography.intel.aws.ec2.security_groups.sync_ec2_security_groupinfo(
            neo4j_session,
            MagicMock(),
            [TEST_REGION],
            account_id,
            update_tag,
            {"UPDATE_TAG": update_tag, "AWS_ID": account_id},
        )


def _range_to_rule_rels(neo4j_session) -> set:
    return check_rels(
        neo4j_session,
        "AWSIpRange",
        "id",
        "AWSIpRule",
        "ruleid",
        "MEMBER_OF_IP_RULE",
        rel_direction_right=True,
    )


def _account_to_range_rels(neo4j_session) -> set:
    return check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "AWSIpRange",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    )


def test_ip_range_shared_across_accounts_is_not_owned(neo4j_session):
    """
    Regression test for https://github.com/cartography-cncf/cartography/issues/2928.

    A CIDR referenced by security group rules in two accounts is one AWSIpRange node.
    It is a reference, not something either account owns, so it must not get a
    (:AWSAccount)-[:RESOURCE]->(:AWSIpRange) edge from either of them.
    """
    neo4j_session.run("MATCH (n) DETACH DELETE n")

    _sync_account(
        neo4j_session,
        ACCOUNT_A,
        [_sg_with_cidrs("sg-aaaa", ACCOUNT_A, [SHARED_CIDR])],
        TEST_UPDATE_TAG,
    )
    _sync_account(
        neo4j_session,
        ACCOUNT_B,
        [_sg_with_cidrs("sg-bbbb", ACCOUNT_B, [SHARED_CIDR])],
        TEST_UPDATE_TAG,
    )

    assert check_nodes(neo4j_session, "AWSIpRange", ["id"]) == {(SHARED_CIDR,)}
    assert _account_to_range_rels(neo4j_session) == set()
    assert _range_to_rule_rels(neo4j_session) == {
        (SHARED_CIDR, "sg-aaaa/IpPermissions/443/443/tcp"),
        (SHARED_CIDR, "sg-aaaa/IpPermissionsEgress/443/443/tcp"),
        (SHARED_CIDR, "sg-bbbb/IpPermissions/443/443/tcp"),
        (SHARED_CIDR, "sg-bbbb/IpPermissionsEgress/443/443/tcp"),
    }


def test_ip_range_cleanup_is_scoped_to_the_synced_account(neo4j_session):
    """
    Without an account to scope it, a generated cleanup would delete every stale
    MEMBER_OF_IP_RULE edge in the graph. Re-syncing account A must leave account B's
    edges alone even though B has not been re-synced with the new update tag.
    """
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _sync_account(
        neo4j_session,
        ACCOUNT_A,
        [_sg_with_cidrs("sg-aaaa", ACCOUNT_A, [SHARED_CIDR, "192.0.2.0/24"])],
        TEST_UPDATE_TAG,
    )
    _sync_account(
        neo4j_session,
        ACCOUNT_B,
        [_sg_with_cidrs("sg-bbbb", ACCOUNT_B, [SHARED_CIDR])],
        TEST_UPDATE_TAG,
    )

    # Account A's rules stop referencing both CIDRs; only A is re-synced.
    _sync_account(
        neo4j_session,
        ACCOUNT_A,
        [_sg_with_cidrs("sg-aaaa", ACCOUNT_A, ["198.51.100.0/24"])],
        TEST_UPDATE_TAG + 1,
    )

    assert _range_to_rule_rels(neo4j_session) == {
        ("198.51.100.0/24", "sg-aaaa/IpPermissions/443/443/tcp"),
        ("198.51.100.0/24", "sg-aaaa/IpPermissionsEgress/443/443/tcp"),
        # Still referenced by account B, so it keeps the edges and the node survives.
        (SHARED_CIDR, "sg-bbbb/IpPermissions/443/443/tcp"),
        (SHARED_CIDR, "sg-bbbb/IpPermissionsEgress/443/443/tcp"),
    }
    # 192.0.2.0/24 is no longer referenced by any rule, so the node is removed.
    assert check_nodes(neo4j_session, "AWSIpRange", ["id"]) == {
        ("198.51.100.0/24",),
        (SHARED_CIDR,),
    }

    # Once account B stops referencing the shared CIDR too, its node is removed.
    _sync_account(
        neo4j_session,
        ACCOUNT_B,
        [_sg_with_cidrs("sg-bbbb", ACCOUNT_B, [])],
        TEST_UPDATE_TAG + 1,
    )
    assert check_nodes(neo4j_session, "AWSIpRange", ["id"]) == {("198.51.100.0/24",)}


def test_legacy_account_to_ip_range_edges_are_removed(neo4j_session):
    """
    Graphs written before the fix still hold RESOURCE edges that no schema draws.
    Each account's sync removes only its own; another account's legacy edge keeps its
    range until that account syncs, even when no rule references the range.
    """
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _sync_account(
        neo4j_session,
        ACCOUNT_A,
        [_sg_with_cidrs("sg-aaaa", ACCOUNT_A, [SHARED_CIDR])],
        TEST_UPDATE_TAG,
    )
    neo4j_session.run(
        """
        MATCH (a:AWSAccount {id: $account_id}), (r:AWSIpRange {id: $cidr})
        MERGE (a)-[:RESOURCE]->(r)
        """,
        account_id=ACCOUNT_A,
        cidr=SHARED_CIDR,
    )
    create_test_account(neo4j_session, ACCOUNT_B, TEST_UPDATE_TAG)
    neo4j_session.run(
        """
        MATCH (b:AWSAccount {id: $account_id})
        MERGE (b)-[:RESOURCE]->(:AWSIpRange {id: '203.0.113.0/24'})
        """,
        account_id=ACCOUNT_B,
    )

    _sync_account(
        neo4j_session,
        ACCOUNT_A,
        [_sg_with_cidrs("sg-aaaa", ACCOUNT_A, [SHARED_CIDR])],
        TEST_UPDATE_TAG + 1,
    )

    assert _account_to_range_rels(neo4j_session) == {(ACCOUNT_B, "203.0.113.0/24")}
    assert check_nodes(neo4j_session, "AWSIpRange", ["id"]) == {
        (SHARED_CIDR,),
        ("203.0.113.0/24",),
    }

    _sync_account(neo4j_session, ACCOUNT_B, [], TEST_UPDATE_TAG + 1)

    assert _account_to_range_rels(neo4j_session) == set()
    assert check_nodes(neo4j_session, "AWSIpRange", ["id"]) == {(SHARED_CIDR,)}
