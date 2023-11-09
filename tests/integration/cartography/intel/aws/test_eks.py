from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.eks
from cartography.intel.aws.eks import sync
from tests.data.aws.eks import DESCRIBE_CLUSTERS
from tests.data.aws.eks import LIST_CLUSTERS
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = '000000000000'
TEST_REGION = 'eu-west-1'
TEST_UPDATE_TAG = 123456789


@patch.object(cartography.intel.aws.eks, 'get_eks_clusters', return_value=LIST_CLUSTERS)
@patch.object(cartography.intel.aws.eks, 'get_eks_describe_cluster', side_effect=DESCRIBE_CLUSTERS)
def test_sync_eks_clusters(mock_describe_clusters, mock_get_clusters, neo4j_session):
    # Arrange
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
    boto3_session = MagicMock()

    # Act
    sync(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {'UPDATE_TAG': TEST_UPDATE_TAG, 'AWS_ID': TEST_ACCOUNT_ID},
    )

    # Assert
    assert check_nodes(neo4j_session, 'EKSCluster', ['id', 'platform_version']) == {
        ('arn:aws:eks:eu-west-1:111111111111:cluster/cluster_1', 'eks.9'),
        ('arn:aws:eks:eu-west-2:222222222222:cluster/cluster_2', 'eks.9'),
    }

    assert check_rels(
        neo4j_session,
        'EKSCluster',
        'id',
        'AWSAccount',
        'id',
        'RESOURCE',
        rel_direction_right=False,
    ) == {
        ('arn:aws:eks:eu-west-1:111111111111:cluster/cluster_1', '000000000000'),
        ('arn:aws:eks:eu-west-2:222222222222:cluster/cluster_2', '000000000000'),
    }
