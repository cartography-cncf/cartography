import cartography.intel.aws.ec2
import tests.data.aws.ec2.security_groups

TEST_ACCOUNT_ID = "000000000000"
TEST_REGION = "eu-north-1"
TEST_UPDATE_TAG = 123456789


def test_load_security_groups(neo4j_session):
    data = tests.data.aws.ec2.security_groups.DESCRIBE_SGS
    cartography.intel.aws.ec2.security_groups.load_ec2_security_groupinfo(
        neo4j_session,
        data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "sg-0fd4fff275d63600f",
        "sg-028e2522c72719996",
        "sg-06c795c66be8937be",
        "sg-053dba35430032a0d",
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
    cartography.intel.aws.ec2.security_groups.load_ec2_security_groupinfo(
        neo4j_session,
        data,
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
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (s:EC2SecurityGroup)-[]-(r:IpRule) RETURN s.id,r.ruleid;
        """,
    )
    actual = {(r["s.id"], r["r.ruleid"]) for r in result}

    assert actual == expected_nodes
