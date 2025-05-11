import cartography.intel.aws.redshift
import tests.data.aws.redshift

TEST_ACCOUNT_ID = "1111"
TEST_REGION = "us-east-1"
TEST_UPDATE_TAG = 123456789


def test_load_redshift_cluster_data(neo4j_session):
    _ensure_local_neo4j_has_test_cluster_data(neo4j_session)

    # Test that the Redshift cluster node was created
    expected_nodes = {
        "arn:aws:redshift:us-east-1:1111:cluster:my-cluster",
    }
    nodes = neo4j_session.run(
        """
        MATCH (n:RedshiftCluster) RETURN n.id;
        """,
    )
    actual_nodes = {n["n.id"] for n in nodes}
    assert actual_nodes == expected_nodes


def test_load_redshift_cluster_and_aws_account(neo4j_session):
    # Create test AWSAccount
    neo4j_session.run(
        """
        MERGE (aws:AWSAccount{id: $aws_account_id})
        ON CREATE SET aws.firstseen = timestamp()
        SET aws.lastupdated = $aws_update_tag
        """,
        aws_account_id=TEST_ACCOUNT_ID,
        aws_update_tag=TEST_UPDATE_TAG,
    )
    _ensure_local_neo4j_has_test_cluster_data(neo4j_session)

    # Test that AWSAccount-to-RedshiftCluster relationships exist
    expected = {
        (TEST_ACCOUNT_ID, "arn:aws:redshift:us-east-1:1111:cluster:my-cluster"),
    }
    result = neo4j_session.run(
        """
        MATCH (n1:AWSAccount)-[:RESOURCE]->(n2:RedshiftCluster) RETURN n1.id, n2.id;
        """,
    )
    actual = {(r["n1.id"], r["n2.id"]) for r in result}
    assert actual == expected


def test_load_redshift_cluster_and_security_group(neo4j_session):
    # Create test EC2 security group
    neo4j_session.run(
        """
        MERGE (aws:EC2SecurityGroup{id: $GroupId})
        ON CREATE SET aws.firstseen = timestamp()
        SET aws.lastupdated = $aws_update_tag
        """,
        GroupId="my-vpc-sg",
        aws_update_tag=TEST_UPDATE_TAG,
    )
    _ensure_local_neo4j_has_test_cluster_data(neo4j_session)

    # Test that RedshiftCluster-to-EC2SecurityGroup relationships exist
    expected = {
        ("my-vpc-sg", "arn:aws:redshift:us-east-1:1111:cluster:my-cluster"),
    }
    result = neo4j_session.run(
        """
        MATCH (n1:EC2SecurityGroup)<-[:MEMBER_OF_EC2_SECURITY_GROUP]-(n2:RedshiftCluster) RETURN n1.id, n2.id;
        """,
    )
    actual = {(r["n1.id"], r["n2.id"]) for r in result}
    assert actual == expected


def test_load_redshift_cluster_and_iam_role(neo4j_session):
    # Create test IAM role
    neo4j_session.run(
        """
        MERGE (aws:AWSPrincipal:AWSRole{arn: $RoleArn})
        ON CREATE SET aws.firstseen = timestamp()
        SET aws.lastupdated = $aws_update_tag
        """,
        RoleArn="arn:aws:iam::1111:role/my-test-role",
        aws_update_tag=TEST_UPDATE_TAG,
    )
    _ensure_local_neo4j_has_test_cluster_data(neo4j_session)

    # Test that RedshiftCluster-to-IAM-role relationships exist
    expected = {
        (
            "arn:aws:iam::1111:role/my-redshift-iam-role",
            "arn:aws:redshift:us-east-1:1111:cluster:my-cluster",
        ),
    }
    result = neo4j_session.run(
        """
        MATCH (n1:AWSPrincipal)<-[:STS_ASSUMEROLE_ALLOW]-(n2:RedshiftCluster) RETURN n1.arn, n2.id;
        """,
    )
    actual = {(r["n1.arn"], r["n2.id"]) for r in result}
    assert actual == expected


def test_load_redshift_cluster_and_vpc(neo4j_session):
    # Create test VPC
    neo4j_session.run(
        """
        MERGE (aws:AWSVpc{id: $VpcId})
        ON CREATE SET aws.firstseen = timestamp()
        SET aws.lastupdated = $aws_update_tag
        """,
        VpcId="my_vpc",
        aws_update_tag=TEST_UPDATE_TAG,
    )
    _ensure_local_neo4j_has_test_cluster_data(neo4j_session)

    # Test that RedshiftCluster-to-VPC relationships exist
    expected = {
        ("my_vpc", "arn:aws:redshift:us-east-1:1111:cluster:my-cluster"),
    }
    result = neo4j_session.run(
        """
        MATCH (n1:AWSVpc)<-[:MEMBER_OF_AWS_VPC]-(n2:RedshiftCluster) RETURN n1.id, n2.id;
        """,
    )
    actual = {(r["n1.id"], r["n2.id"]) for r in result}
    assert actual == expected


def _ensure_local_neo4j_has_test_cluster_data(neo4j_session):
    """Pre-load the Neo4j instance with sample Redshift data"""
    clusters = tests.data.aws.redshift.CLUSTERS
    cartography.intel.aws.redshift.transform_redshift_cluster_data(
        clusters,
        TEST_REGION,
        TEST_ACCOUNT_ID,
    )
    cartography.intel.aws.redshift.load_redshift_cluster_data(
        neo4j_session,
        clusters,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )
