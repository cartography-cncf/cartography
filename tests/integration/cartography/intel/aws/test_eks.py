from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.eks
from cartography.intel.aws.eks import sync
from tests.data.aws.eks import ACCESS_ENTRIES
from tests.data.aws.eks import DESCRIBE_CLUSTERS
from tests.data.aws.eks import LIST_CLUSTERS
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "000000000000"
TEST_REGION = "eu-west-1"
TEST_UPDATE_TAG = 123456789


@patch.object(cartography.intel.aws.eks, "get_eks_clusters", return_value=LIST_CLUSTERS)
@patch.object(
    cartography.intel.aws.eks,
    "get_eks_access_entries",
    side_effect=ACCESS_ENTRIES,
)
@patch.object(
    cartography.intel.aws.eks,
    "get_eks_describe_cluster",
    side_effect=DESCRIBE_CLUSTERS,
)
def test_sync_eks_clusters(
    mock_describe_clusters,
    mock_get_access_entries,
    mock_get_clusters,
    neo4j_session,
):
    # Arrange
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
    neo4j_session.run(
        """
        MERGE (role:AWSRole:AWSPrincipal {
            arn: 'arn:aws:iam::111111111111:role/EKSAdminRole'
        })
        SET role.id = role.arn, role.lastupdated = $update_tag
        MERGE (list_only_role:AWSRole:AWSPrincipal {
            arn: 'arn:aws:iam::111111111111:role/EKSListOnlyRole'
        })
        SET list_only_role.id = list_only_role.arn,
            list_only_role.lastupdated = $update_tag
        """,
        update_tag=TEST_UPDATE_TAG,
    )
    boto3_session = MagicMock()

    # Act
    sync(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Assert
    assert check_nodes(
        neo4j_session,
        "AWSEKSCluster",
        ["id", "platform_version", "authentication_mode"],
    ) == {
        (
            "arn:aws:eks:eu-west-1:111111111111:cluster/cluster_1",
            "eks.9",
            "API_AND_CONFIG_MAP",
        ),
        (
            "arn:aws:eks:eu-west-2:222222222222:cluster/cluster_2",
            "eks.9",
            "CONFIG_MAP",
        ),
    }
    assert check_nodes(
        neo4j_session,
        "AWSEKSAccessEntry",
        ["id", "arn", "principal_arn", "username", "type"],
    ) == {
        (
            "arn:aws:eks:eu-west-1:111111111111:cluster/cluster_1/"
            "access-entry/arn:aws:iam::111111111111:role/EKSAdminRole",
            "arn:aws:eks:eu-west-1:111111111111:access-entry/"
            "cluster_1/role/111111111111/EKSAdminRole/ae-12345",
            "arn:aws:iam::111111111111:role/EKSAdminRole",
            "eks-admin",
            "STANDARD",
        ),
        (
            "arn:aws:eks:eu-west-1:111111111111:cluster/cluster_1/"
            "access-entry/arn:aws:iam::111111111111:role/EKSListOnlyRole",
            None,
            "arn:aws:iam::111111111111:role/EKSListOnlyRole",
            None,
            None,
        ),
    }
    groups_result = neo4j_session.run(
        """
        MATCH (entry:AWSEKSAccessEntry {id: $id})
        RETURN entry.kubernetes_groups AS groups
        """,
        id=(
            "arn:aws:eks:eu-west-1:111111111111:cluster/cluster_1/"
            "access-entry/arn:aws:iam::111111111111:role/EKSAdminRole"
        ),
    )
    assert groups_result.single()["groups"] == ["system:masters"]
    assert check_nodes(
        neo4j_session,
        "AWSEKSCluster",
        [
            "id",
            "certificate_authority_data_present",
            "certificate_authority_parse_status",
            "certificate_authority_sha256_fingerprint",
        ],
    ) == {
        (
            "arn:aws:eks:eu-west-1:111111111111:cluster/cluster_1",
            True,
            "parsed",
            "4680a4733878c73936ce9ee5330845253d0514370efbecaaa322068aa4538260",
        ),
        (
            "arn:aws:eks:eu-west-2:222222222222:cluster/cluster_2",
            True,
            "invalid_base64",
            None,
        ),
    }

    assert check_rels(
        neo4j_session,
        "AWSEKSCluster",
        "id",
        "AWSAccount",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        ("arn:aws:eks:eu-west-1:111111111111:cluster/cluster_1", "000000000000"),
        ("arn:aws:eks:eu-west-2:222222222222:cluster/cluster_2", "000000000000"),
    }
    assert check_rels(
        neo4j_session,
        "AWSEKSAccessEntry",
        "id",
        "AWSAccount",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        (
            "arn:aws:eks:eu-west-1:111111111111:cluster/cluster_1/"
            "access-entry/arn:aws:iam::111111111111:role/EKSAdminRole",
            "000000000000",
        ),
        (
            "arn:aws:eks:eu-west-1:111111111111:cluster/cluster_1/"
            "access-entry/arn:aws:iam::111111111111:role/EKSListOnlyRole",
            "000000000000",
        ),
    }
    assert check_rels(
        neo4j_session,
        "AWSEKSCluster",
        "id",
        "AWSEKSAccessEntry",
        "id",
        "HAS_ACCESS_ENTRY",
    ) == {
        (
            "arn:aws:eks:eu-west-1:111111111111:cluster/cluster_1",
            "arn:aws:eks:eu-west-1:111111111111:cluster/cluster_1/"
            "access-entry/arn:aws:iam::111111111111:role/EKSAdminRole",
        ),
        (
            "arn:aws:eks:eu-west-1:111111111111:cluster/cluster_1",
            "arn:aws:eks:eu-west-1:111111111111:cluster/cluster_1/"
            "access-entry/arn:aws:iam::111111111111:role/EKSListOnlyRole",
        ),
    }
    assert check_rels(
        neo4j_session,
        "AWSRole",
        "arn",
        "AWSEKSAccessEntry",
        "id",
        "GRANTED_ACCESS_TO",
    ) == {
        (
            "arn:aws:iam::111111111111:role/EKSAdminRole",
            "arn:aws:eks:eu-west-1:111111111111:cluster/cluster_1/"
            "access-entry/arn:aws:iam::111111111111:role/EKSAdminRole",
        ),
        (
            "arn:aws:iam::111111111111:role/EKSListOnlyRole",
            "arn:aws:eks:eu-west-1:111111111111:cluster/cluster_1/"
            "access-entry/arn:aws:iam::111111111111:role/EKSListOnlyRole",
        ),
    }
    mock_get_access_entries.assert_any_call(
        boto3_session,
        TEST_REGION,
        "cluster_1",
        "API_AND_CONFIG_MAP",
    )
    mock_get_access_entries.assert_any_call(
        boto3_session,
        TEST_REGION,
        "cluster_2",
        "CONFIG_MAP",
    )
