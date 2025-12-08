from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.gcp.compute
import cartography.intel.gcp.iam
import cartography.intel.gcp.permission_relationships
import cartography.intel.gcp.policy_bindings
import cartography.intel.gcp.storage
import cartography.intel.gsuite.groups
import cartography.intel.gsuite.users
from tests.data.gcp.permission_relationships import MOCK_COMPUTE_INSTANCES
from tests.data.gcp.permission_relationships import MOCK_PERMISSION_RELATIONSHIPS_YAML
from tests.data.gcp.permission_relationships import MOCK_STORAGE_BUCKETS
from tests.data.gcp.policy_bindings import MOCK_GSUITE_GROUP_MEMBERS
from tests.data.gcp.policy_bindings import MOCK_GSUITE_GROUPS
from tests.data.gcp.policy_bindings import MOCK_GSUITE_USERS
from tests.data.gcp.policy_bindings import MOCK_IAM_ROLES
from tests.data.gcp.policy_bindings import MOCK_IAM_SERVICE_ACCOUNTS
from tests.data.gcp.policy_bindings import MOCK_POLICY_BINDINGS_RESPONSE
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_PROJECT_ID = "project-123"
TEST_UPDATE_TAG = 123456789
COMMON_JOB_PARAMS = {
    "UPDATE_TAG": TEST_UPDATE_TAG,
    "ORG_RESOURCE_NAME": "organizations/1337",
    "PROJECT_ID": TEST_PROJECT_ID,
    "gcp_permission_relationships_file": "dummy_path",  # Will be mocked!
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
    cartography.intel.gcp.permission_relationships,
    "parse_permission_relationships_file",
    return_value=MOCK_PERMISSION_RELATIONSHIPS_YAML,
)
@patch.object(
    cartography.intel.gcp.compute,
    "get_gcp_instance_responses",
    return_value=[MOCK_COMPUTE_INSTANCES],
)
@patch.object(
    cartography.intel.gcp.compute,
    "get_zones_in_project",
    return_value=[{"name": "us-east1-b"}],
)
@patch.object(
    cartography.intel.gcp.storage,
    "get_gcp_buckets",
    return_value=MOCK_STORAGE_BUCKETS,
)
@patch.object(
    cartography.intel.gcp.policy_bindings,
    "get_policy_bindings",
    return_value=MOCK_POLICY_BINDINGS_RESPONSE,
)
@patch.object(
    cartography.intel.gsuite.groups,
    "get_members_for_groups",
    return_value=MOCK_GSUITE_GROUP_MEMBERS,
)
@patch.object(
    cartography.intel.gsuite.groups,
    "get_all_groups",
    return_value=MOCK_GSUITE_GROUPS,
)
@patch.object(
    cartography.intel.gsuite.users,
    "get_all_users",
    return_value=MOCK_GSUITE_USERS,
)
@patch.object(
    cartography.intel.gcp.iam,
    "get_gcp_roles",
    return_value=MOCK_IAM_ROLES,
)
@patch.object(
    cartography.intel.gcp.iam,
    "get_gcp_service_accounts",
    return_value=MOCK_IAM_SERVICE_ACCOUNTS,
)
def test_sync_gcp_permission_relationships(
    mock_get_service_accounts,
    mock_get_roles,
    mock_get_all_users,
    mock_get_all_groups,
    mock_get_group_members,
    mock_get_policy_bindings,
    mock_get_buckets,
    mock_get_zones,
    mock_get_instance_responses,
    mock_parse_yaml,
    neo4j_session,
):
    """
    Test that GCP permission relationships sync creates the expected nodes and relationships.
    """
    # ARRANGE
    _create_test_project(neo4j_session)
    mock_iam_client = MagicMock()
    mock_admin_resource = MagicMock()
    mock_storage_client = MagicMock()
    mock_compute_client = MagicMock()
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

    cartography.intel.gcp.policy_bindings.sync(
        neo4j_session,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        COMMON_JOB_PARAMS,
        mock_asset_client,
    )

    cartography.intel.gcp.storage.sync_gcp_buckets(
        neo4j_session,
        mock_storage_client,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        COMMON_JOB_PARAMS,
    )

    cartography.intel.gcp.compute.sync_gcp_instances(
        neo4j_session,
        mock_compute_client,
        TEST_PROJECT_ID,
        [{"name": "us-east1-b"}],
        TEST_UPDATE_TAG,
        COMMON_JOB_PARAMS,
    )

    # ACT
    cartography.intel.gcp.permission_relationships.sync(
        neo4j_session,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        COMMON_JOB_PARAMS,
    )

    # ASSERT
    # Check that storage bucket node exists
    assert check_nodes(neo4j_session, "GCPBucket", ["id"]) == {
        ("test-bucket",),
    }

    # Check that compute instance node exists
    assert check_nodes(
        neo4j_session,
        "GCPInstance",
        ["id"],
    ) == {
        ("projects/project-123/zones/us-east1-b/instances/instance-1",),
    }

    # Check permission relationships: GCPPrincipal CAN_READ GCPBucket
    # alice@example.com has roles/storage.objectViewer on test-bucket
    # which includes storage.objects.get permission
    assert check_rels(
        neo4j_session,
        "GCPPrincipal",
        "email",
        "GCPBucket",
        "id",
        "CAN_READ",
        rel_direction_right=True,
    ) == {
        ("alice@example.com", "test-bucket"),
    }

    # Check permission relationships: GCPPrincipal CAN_GET_ACCELERATOR_TYPES GCPInstance
    # alice@example.com has roles/editor on project which includes compute.acceleratorTypes.get
    # sa@project-123.iam.gserviceaccount.com has roles/editor on project which includes compute.acceleratorTypes.get
    assert check_rels(
        neo4j_session,
        "GCPPrincipal",
        "email",
        "GCPInstance",
        "id",
        "CAN_GET_ACCELERATOR_TYPES",
        rel_direction_right=True,
    ) == {
        (
            "alice@example.com",
            "projects/project-123/zones/us-east1-b/instances/instance-1",
        ),
        (
            "sa@project-123.iam.gserviceaccount.com",
            "projects/project-123/zones/us-east1-b/instances/instance-1",
        ),
    }
