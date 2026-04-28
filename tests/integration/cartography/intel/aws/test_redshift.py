from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.redshift
from tests.data.aws.redshift import CLUSTERS
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "1111"
TEST_REGION = "us-east-1"
TEST_UPDATE_TAG = 123456789


def _create_prerequisite_nodes(neo4j_session):
    """Pre-create nodes that Redshift clusters will connect to via other_relationships."""
    neo4j_session.run(
        "MERGE (sg:EC2SecurityGroup {id: 'my-vpc-sg'})"
        " ON CREATE SET sg.firstseen = timestamp()",
    )
    neo4j_session.run(
        "MERGE (p:AWSPrincipal {arn: 'arn:aws:iam::1111:role/my-redshift-iam-role'})"
        " ON CREATE SET p.firstseen = timestamp()",
    )
    neo4j_session.run(
        "MERGE (v:AWSVpc {id: 'my_vpc'})" " ON CREATE SET v.firstseen = timestamp()",
    )


@patch.object(
    cartography.intel.aws.redshift,
    "get_redshift_cluster_data",
    return_value=CLUSTERS,
)
def test_sync_redshift_clusters(mock_get_data, neo4j_session):
    """
    Ensure that sync() creates RedshiftCluster nodes and all expected relationships.
    """
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
    _create_prerequisite_nodes(neo4j_session)

    cartography.intel.aws.redshift.sync(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Verify RedshiftCluster node
    assert check_nodes(neo4j_session, "RedshiftCluster", ["id"]) == {
        ("arn:aws:redshift:us-east-1:1111:cluster:my-cluster",),
    }

    # Verify AWSAccount -[:RESOURCE]-> RedshiftCluster
    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "RedshiftCluster",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (TEST_ACCOUNT_ID, "arn:aws:redshift:us-east-1:1111:cluster:my-cluster"),
    }

    # Verify RedshiftCluster -[:MEMBER_OF_EC2_SECURITY_GROUP]-> EC2SecurityGroup
    assert check_rels(
        neo4j_session,
        "RedshiftCluster",
        "id",
        "EC2SecurityGroup",
        "id",
        "MEMBER_OF_EC2_SECURITY_GROUP",
        rel_direction_right=True,
    ) == {
        ("arn:aws:redshift:us-east-1:1111:cluster:my-cluster", "my-vpc-sg"),
    }

    # Verify RedshiftCluster -[:STS_ASSUMEROLE_ALLOW]-> AWSPrincipal
    assert check_rels(
        neo4j_session,
        "RedshiftCluster",
        "id",
        "AWSPrincipal",
        "arn",
        "STS_ASSUMEROLE_ALLOW",
        rel_direction_right=True,
    ) == {
        (
            "arn:aws:redshift:us-east-1:1111:cluster:my-cluster",
            "arn:aws:iam::1111:role/my-redshift-iam-role",
        ),
    }

    # Verify RedshiftCluster -[:MEMBER_OF_AWS_VPC]-> AWSVpc
    assert check_rels(
        neo4j_session,
        "RedshiftCluster",
        "id",
        "AWSVpc",
        "id",
        "MEMBER_OF_AWS_VPC",
        rel_direction_right=True,
    ) == {
        ("arn:aws:redshift:us-east-1:1111:cluster:my-cluster", "my_vpc"),
    }
