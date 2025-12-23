from unittest.mock import MagicMock, patch
from collections import namedtuple

import cartography.intel.aws.ec2.security_groups
import tests.data.aws.ec2.security_groups
import tests.data.aws.ec2.security_group_rules
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "000000000000"
TEST_REGION = "us-east-1"
TEST_UPDATE_TAG = 123456789


def test_load_security_groups(neo4j_session):
    # Arrange
    Ec2SecurityGroupData = namedtuple(
        "Ec2SecurityGroupData",
        ["groups", "inbound_rules", "egress_rules", "ranges"]
    )

    # Create test AWS account first
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    # Mock the security group rules API response
    def mock_get_rules_side_effect(boto3_session, region, group_id):
        # Return the rules for the specified group_id or an empty list if not found
        return tests.data.aws.ec2.security_group_rules.DESCRIBE_SECURITY_GROUP_RULES.get(group_id, [])

    # Create a mock boto3 session
    boto3_session = MagicMock()

    # Apply the mock
    with patch.object(
        cartography.intel.aws.ec2.security_groups,
        "get_ec2_security_group_rules",
        side_effect=mock_get_rules_side_effect,
    ) as mock_get_rules:
        # First transform the data to include rules
        transformed_data = cartography.intel.aws.ec2.security_groups.transform_ec2_security_group_data(
            tests.data.aws.ec2.security_groups.DESCRIBE_SGS,
            boto3_session,
            TEST_REGION,
        )

        # Act - Load security groups with the transformed data
        cartography.intel.aws.ec2.security_groups.load_ec2_security_groupinfo(
            neo4j_session,
            transformed_data,
            TEST_REGION,
            TEST_ACCOUNT_ID,
            TEST_UPDATE_TAG,
        )

    # Verify security group nodes were created
    result = neo4j_session.run("""
        MATCH (sg:EC2SecurityGroup)
        RETURN sg.id, sg.groupid, sg.name
    """)
    actual_nodes = {(r["sg.id"], r["sg.groupid"], r["sg.name"]) for r in result}

    expected_nodes = {
        ("sg-028e2522c72719996", "sg-028e2522c72719996", "sq-vpc2-id1"),
        ("sg-0fd4fff275d63600f", "sg-0fd4fff275d63600f", "default"),
        ("sg-06c795c66be8937be", "sg-06c795c66be8937be", "sq-vpc1-id1"),
        ("sg-053dba35430032a0d", "sg-053dba35430032a0d", "default"),
        ("sg-web-server-12345", "sg-web-server-12345", "web-server-sg"),
    }

    assert actual_nodes == expected_nodes, "Security group nodes do not match expected"

    # Verify security group properties using direct Cypher query
    result = neo4j_session.run(
        "MATCH (sg:EC2SecurityGroup{id: $sg_id}) RETURN sg",
        {"sg_id": "sg-028e2522c72719996"}
    )
    sg = result.single()
    assert sg is not None, "Security group not found in the database"
    sg = sg["sg"]
    assert sg["description"] == "security group vpc2-id1", "Unexpected security group description"
    assert sg["name"] == "sq-vpc2-id1", f"Unexpected security group name: {sg.get('name')}"
    assert sg["groupid"] == "sg-028e2522c72719996", "Unexpected security group ID"

    # Verify relationship to AWS account
    result = neo4j_session.run("""
        MATCH (sg:EC2SecurityGroup{id: $sg_id})<-[:RESOURCE]-(:AWSAccount{id: $account_id})
        RETURN count(*) as count
    """, {"sg_id": "sg-028e2522c72719996", "account_id": TEST_ACCOUNT_ID})
    assert result.single()["count"] == 1, "Security group should be connected to AWS account"

    # Verify region property
    assert sg["region"] == TEST_REGION, f"Expected region {TEST_REGION}, got {sg.get('region')}"

    # Verify security group rules were created
    result = neo4j_session.run("""
        MATCH (r:IpRule)
        RETURN r.ruleid, r.groupid, r.protocol, r.fromport, r.toport
    """)

    # Verify specific rules exist
    result = neo4j_session.run("""
        MATCH (r:IpRule {groupid: 'sg-028e2522c72719996'})
        RETURN count(*) as count
    """)
    assert result.single()["count"] > 0, "Expected rules for security group sg-028e2522c72719996"

    # Verify the expected number of rules (4) for the security group
    result = neo4j_session.run("""
        MATCH (r:IpRule {groupid: 'sg-028e2522c72719996'})
        RETURN count(*) as count
    """)
    assert result.single()["count"] == 4, "Expected 4 IpRule nodes for security group sg-028e2522c72719996"

    # Verify the security group exists
    result = neo4j_session.run("""
        MATCH (sg:EC2SecurityGroup {groupid: 'sg-028e2522c72719996'})
        RETURN count(*) as count
    """)
    assert result.single()["count"] == 1, "Expected 1 EC2SecurityGroup node for group sg-028e2522c72719996"

    # Verify relationship between rule and security group exists
    result = neo4j_session.run("""
        MATCH (r:IpRule {groupid: 'sg-028e2522c72719996'})-[rel]-(sg:EC2SecurityGroup {groupid: 'sg-028e2522c72719996'})
        RETURN count(*) as count
    """)
    assert result.single()["count"] > 0, "Expected relationship between IpRule and EC2SecurityGroup"

    # Query all IpRule nodes to verify presence
    all_rules = neo4j_session.run("""
        MATCH (r:IpRule)
        RETURN r.ruleid as ruleid, r.protocol as protocol, 
               r.fromport as fromport, r.toport as toport,
               r.isegress as isegress
    """)

    # Verify specific rules and their properties
    expected_rules = [
        {
            'ruleid': 'sgr-0123456789abcdef0',
            'protocol': 'tcp',
            'fromport': 80,
            'toport': 80,
            'isegress': False,  # ingress rule (IsEgress=False)
        },
        {
            'ruleid': 'sgr-0123456789abcdef1',
            'protocol': 'tcp',
            'fromport': 443,
            'toport': 443,
            'isegress': False,  # ingress rule (IsEgress=False)
        },
        {
            'ruleid': 'sgr-0123456789abcdef2',
            'protocol': 'tcp',
            'fromport': 80,
            'toport': 80,
            'isegress': True,   # egress rule (IsEgress=True)
        },
        {
            'ruleid': 'sgr-0123456789abcdef3',
            'protocol': '-1',
            'fromport': None,
            'toport': None,
            'isegress': True,   # egress rule (IsEgress=True)
        },
    ]

    # Verify each expected rule exists and has correct properties
    for expected_rule in expected_rules:
        result = neo4j_session.run("""
            MATCH (r:IpRule {ruleid: $ruleid})
            RETURN r.protocol as protocol, 
                   r.fromport as fromport, 
                   r.toport as toport,
                   r.isegress as isegress
        """, ruleid=expected_rule['ruleid'])

        actual_rule = result.single()
        assert actual_rule is not None, f"Rule {expected_rule['ruleid']} not found in database"

        # Print actual and expected values for debugging
        print(f"\n=== DEBUG: Checking rule {expected_rule['ruleid']} ===")
        print(f"Expected: {expected_rule}")
        print(f"Actual:   {dict(actual_rule)}")

        for key, expected_value in expected_rule.items():
            if key != 'ruleid':  # We already matched on ruleid
                actual_value = actual_rule[key]
                assert actual_value == expected_value, \
                    f"Mismatch in rule {expected_rule['ruleid']} for {key}: expected {expected_value}, got {actual_value}"

    # Verify IP ranges are properly linked to rules
    expected_ranges = [
        {'ruleid': 'sgr-0123456789abcdef0', 'range': '203.0.113.0/24'},
        {'ruleid': 'sgr-0123456789abcdef1', 'range': '203.0.113.0/24'},
        {'ruleid': 'sgr-0123456789abcdef2', 'range': '0.0.0.0/0'},
        {'ruleid': 'sgr-0123456789abcdef3', 'range': '0.0.0.0/0'},
    ]

    for expected_range in expected_ranges:
        result = neo4j_session.run("""
            MATCH (r:IpRule {ruleid: $ruleid})<-[:MEMBER_OF_IP_RULE]-(ip:IpRange {range: $range})
            RETURN count(*) as count
        """, ruleid=expected_range['ruleid'], range=expected_range['range'])
        assert result.single()["count"] > 0, f"Expected IP range {expected_range['range']} for rule {expected_range['ruleid']}"

    # Verify AWS account relationships
    result = neo4j_session.run("""
        MATCH (r:IpRule)<-[:RESOURCE]-(a:AWSAccount {id: $account_id})
        RETURN count(*) as count
    """, account_id=TEST_ACCOUNT_ID)
    assert result.single()["count"] == 4, "Expected 4 IpRule nodes to be connected to the AWS account"
