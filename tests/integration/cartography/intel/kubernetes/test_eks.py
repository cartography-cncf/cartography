import pytest
from unittest.mock import patch, MagicMock
from kubernetes.client.models import V1ConfigMap

from cartography.intel.kubernetes.eks import sync as eks_sync
from cartography.intel.aws.iam import load_roles
from tests.data.kubernetes.eks import (
    AWS_AUTH_CONFIGMAP_DATA,
    MOCK_AWS_ROLES,
    TEST_CLUSTER_NAME,
    TEST_CLUSTER_ID,
    TEST_UPDATE_TAG,
    TEST_ACCOUNT_ID,
)
from tests.integration.util import check_rels


def create_mock_aws_auth_configmap():
    """Create a mock V1ConfigMap object for testing."""
    return V1ConfigMap(
        api_version="v1",
        kind="ConfigMap",
        metadata={
            "name": "aws-auth",
            "namespace": "kube-system"
        },
        data=AWS_AUTH_CONFIGMAP_DATA
    )


def test_eks_sync_creates_aws_role_relationships(neo4j_session):
    """
    Test that EKS sync creates the expected AWS Role to Kubernetes User/Group relationships.
    """
    # Arrange: Create AWS Account first (required for role loading)
    neo4j_session.run(
        """
        MERGE (aa:AWSAccount{id: $account_id})
        ON CREATE SET aa.firstseen = timestamp()
        SET aa.lastupdated = $update_tag
        """,
        account_id=TEST_ACCOUNT_ID,
        update_tag=TEST_UPDATE_TAG,
    )
    
    # Arrange: Set up prerequisite AWS Roles in the graph
    load_roles(
        neo4j_session,
        MOCK_AWS_ROLES,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )
    
    # Arrange: Create mock K8s client that returns our test ConfigMap
    mock_k8s_client = MagicMock()
    mock_k8s_client.name = TEST_CLUSTER_NAME
    mock_k8s_client.core.read_namespaced_config_map.return_value = create_mock_aws_auth_configmap()
    
    # Act: Run EKS sync
    eks_sync(
        neo4j_session,
        mock_k8s_client,
        TEST_UPDATE_TAG,
        TEST_CLUSTER_ID,
        TEST_CLUSTER_NAME,
    )
    
    # Assert: Verify AWS Role to Kubernetes User relationships
    expected_user_relationships = {
        ("arn:aws:iam::123456789012:role/EKSDevRole", "test-cluster/dev-user"),
        ("arn:aws:iam::123456789012:role/EKSAdminRole", "test-cluster/admin-user"),
        ("arn:aws:iam::123456789012:role/EKSViewerRole", "test-cluster/viewer-user"),
    }
    
    assert (
        check_rels(
            neo4j_session,
            "AWSRole",
            "arn",
            "KubernetesUser",
            "id",
            "MAPS_TO",
        )
        == expected_user_relationships
    )
    
    # Assert: Verify AWS Role to Kubernetes Group relationships
    expected_group_relationships = {
        ("arn:aws:iam::123456789012:role/EKSDevRole", "test-cluster/developers"),
        ("arn:aws:iam::123456789012:role/EKSDevRole", "test-cluster/staging-access"),
        ("arn:aws:iam::123456789012:role/EKSAdminRole", "test-cluster/system:masters"),
        ("arn:aws:iam::123456789012:role/EKSViewerRole", "test-cluster/view-only"),
        ("arn:aws:iam::123456789012:role/EKSViewerRole", "test-cluster/read-access"),
        ("arn:aws:iam::123456789012:role/EKSGroupOnlyRole", "test-cluster/ci-cd"),
        ("arn:aws:iam::123456789012:role/EKSGroupOnlyRole", "test-cluster/automation"),
    }
    
    assert (
        check_rels(
            neo4j_session,
            "AWSRole", 
            "arn",
            "KubernetesGroup",
            "id",
            "MAPS_TO",
        )
        == expected_group_relationships
    ) 