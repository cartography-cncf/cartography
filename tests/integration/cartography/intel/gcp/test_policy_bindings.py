from unittest.mock import MagicMock
from unittest.mock import patch

from google.api_core.exceptions import PermissionDenied

import cartography.intel.gcp.iam
import cartography.intel.gcp.policy_bindings
import cartography.intel.gsuite.groups
import cartography.intel.gsuite.users
import tests.data.gcp.policy_bindings
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_PROJECT_ID = "project-123"
TEST_UPDATE_TAG = 123456789
COMMON_JOB_PARAMS = {
    "UPDATE_TAG": TEST_UPDATE_TAG,
    "ORG_RESOURCE_NAME": "organizations/1337",
    "PROJECT_ID": TEST_PROJECT_ID,
}
GSUITE_COMMON_PARAMS = {
    **COMMON_JOB_PARAMS,
    "CUSTOMER_ID": "customer-123",
}


def _create_test_project(neo4j_session):
    """Create a test GCP project node."""
    neo4j_session.run(
        """
        MERGE (project:GCPProject{id: $project_id})
        ON CREATE SET project.firstseen = timestamp()
        SET project.lastupdated = $update_tag
        """,
        project_id=TEST_PROJECT_ID,
        update_tag=TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.gcp.policy_bindings,
    "get_policy_bindings",
    return_value=tests.data.gcp.policy_bindings.MOCK_POLICY_BINDINGS_RESPONSE,
)
@patch.object(
    cartography.intel.gsuite.groups,
    "get_members_for_groups",
    return_value=tests.data.gcp.policy_bindings.MOCK_GSUITE_GROUP_MEMBERS,
)
@patch.object(
    cartography.intel.gsuite.groups,
    "get_all_groups",
    return_value=tests.data.gcp.policy_bindings.MOCK_GSUITE_GROUPS,
)
@patch.object(
    cartography.intel.gsuite.users,
    "get_all_users",
    return_value=tests.data.gcp.policy_bindings.MOCK_GSUITE_USERS,
)
@patch.object(
    cartography.intel.gcp.iam,
    "get_gcp_roles",
    return_value=tests.data.gcp.policy_bindings.MOCK_IAM_ROLES,
)
@patch.object(
    cartography.intel.gcp.iam,
    "get_gcp_service_accounts",
    return_value=tests.data.gcp.policy_bindings.MOCK_IAM_SERVICE_ACCOUNTS,
)
def test_sync_gcp_policy_bindings(
    mock_get_service_accounts,
    mock_get_roles,
    mock_get_all_users,
    mock_get_all_groups,
    mock_get_group_members,
    mock_get_policy_bindings,
    neo4j_session,
):
    """
    Test that GCP policy bindings sync creates the expected nodes and relationships.
    """
    # ARRANGE
    _create_test_project(neo4j_session)
    mock_iam_client = MagicMock()
    mock_admin_resource = MagicMock()
    mock_asset_client = MagicMock()

    cartography.intel.gcp.iam.sync(
        neo4j_session,
        mock_iam_client,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        COMMON_JOB_PARAMS,
    )

    cartography.intel.gsuite.users.sync_gsuite_users(
        neo4j_session,
        mock_admin_resource,
        TEST_UPDATE_TAG,
        GSUITE_COMMON_PARAMS,
    )

    cartography.intel.gsuite.groups.sync_gsuite_groups(
        neo4j_session,
        mock_admin_resource,
        TEST_UPDATE_TAG,
        GSUITE_COMMON_PARAMS,
    )

    # ACT
    cartography.intel.gcp.policy_bindings.sync(
        neo4j_session,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        COMMON_JOB_PARAMS,
        mock_asset_client,
    )

    # ASSERT
    # Check GCP policy binding nodes
    assert check_nodes(
        neo4j_session, "GCPPolicyBinding", ["id", "role", "resource_type"]
    ) == {
        (
            "//cloudresourcemanager.googleapis.com/projects/project-123_roles/editor",
            "roles/editor",
            "project",
        ),
        (
            "//cloudresourcemanager.googleapis.com/projects/project-123_roles/viewer",
            "roles/viewer",
            "project",
        ),
        (
            "//cloudresourcemanager.googleapis.com/projects/project-123_roles/storage.admin_5982c9d5",
            "roles/storage.admin",
            "project",
        ),
        (
            "//storage.googleapis.com/buckets/test-bucket_roles/storage.objectViewer",
            "roles/storage.objectViewer",
            "resource",
        ),
    }

    # Check GCPProject to GCPPolicyBinding relationships
    assert check_rels(
        neo4j_session,
        "GCPProject",
        "id",
        "GCPPolicyBinding",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (
            TEST_PROJECT_ID,
            "//cloudresourcemanager.googleapis.com/projects/project-123_roles/editor",
        ),
        (
            TEST_PROJECT_ID,
            "//cloudresourcemanager.googleapis.com/projects/project-123_roles/viewer",
        ),
        (
            TEST_PROJECT_ID,
            "//cloudresourcemanager.googleapis.com/projects/project-123_roles/storage.admin_5982c9d5",
        ),
        (
            TEST_PROJECT_ID,
            "//storage.googleapis.com/buckets/test-bucket_roles/storage.objectViewer",
        ),
    }

    # Check GCPPrincipal to GCPPolicyBinding relationships
    assert check_rels(
        neo4j_session,
        "GCPPrincipal",
        "email",
        "GCPPolicyBinding",
        "id",
        "HAS_ALLOW_POLICY",
        rel_direction_right=True,
    ) == {
        # GSuite users
        (
            "alice@example.com",
            "//cloudresourcemanager.googleapis.com/projects/project-123_roles/editor",
        ),
        (
            "alice@example.com",
            "//storage.googleapis.com/buckets/test-bucket_roles/storage.objectViewer",
        ),
        (
            "bob@example.com",
            "//cloudresourcemanager.googleapis.com/projects/project-123_roles/storage.admin_5982c9d5",
        ),
        # IAM service account
        (
            "sa@project-123.iam.gserviceaccount.com",
            "//cloudresourcemanager.googleapis.com/projects/project-123_roles/editor",
        ),
        # GSuite group
        (
            "viewers@example.com",
            "//cloudresourcemanager.googleapis.com/projects/project-123_roles/viewer",
        ),
    }

    # Check GCPPolicyBinding to GCPRole relationships
    assert check_rels(
        neo4j_session,
        "GCPPolicyBinding",
        "id",
        "GCPRole",
        "name",
        "GRANTS_ROLE",
        rel_direction_right=True,
    ) == {
        (
            "//cloudresourcemanager.googleapis.com/projects/project-123_roles/editor",
            "roles/editor",
        ),
        (
            "//cloudresourcemanager.googleapis.com/projects/project-123_roles/viewer",
            "roles/viewer",
        ),
        (
            "//cloudresourcemanager.googleapis.com/projects/project-123_roles/storage.admin_5982c9d5",
            "roles/storage.admin",
        ),
        (
            "//storage.googleapis.com/buckets/test-bucket_roles/storage.objectViewer",
            "roles/storage.objectViewer",
        ),
    }


@patch.object(
    cartography.intel.gcp.policy_bindings,
    "get_policy_bindings",
    side_effect=PermissionDenied(
        "Missing cloudasset.assets.analyzeIamPolicy permission"
    ),
)
def test_sync_gcp_policy_bindings_permission_denied(
    mock_get_policy_bindings,
    neo4j_session,
):
    """
    Test that policy bindings sync handles PermissionDenied gracefully.
    When the user lacks org-level cloudasset.viewer role, sync should return False
    and not raise an exception.
    """
    # ARRANGE
    _create_test_project(neo4j_session)
    mock_asset_client = MagicMock()

    # ACT
    result = cartography.intel.gcp.policy_bindings.sync(
        neo4j_session,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        COMMON_JOB_PARAMS,
        mock_asset_client,
    )

    # ASSERT - sync should return False and not raise an exception
    assert result is False
    mock_get_policy_bindings.assert_called_once()
