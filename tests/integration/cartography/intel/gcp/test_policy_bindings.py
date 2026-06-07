from unittest.mock import MagicMock
from unittest.mock import patch

from google.api_core.exceptions import PermissionDenied

import cartography.intel.gcp.crm.folders
import cartography.intel.gcp.crm.orgs
import cartography.intel.gcp.crm.projects
import cartography.intel.gcp.iam
import cartography.intel.gcp.policy_bindings
import cartography.intel.gsuite.groups
import cartography.intel.gsuite.users
import tests.data.gcp.crm
import tests.data.gcp.policy_bindings
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_PROJECT_ID = "project-abc"
TEST_UPDATE_TAG = 123456789
TEST_FOLDER_ID = tests.data.gcp.crm.GCP_FOLDERS[0]["name"]
TEST_POLICY_BINDING_GSUITE_USERS = tests.data.gcp.policy_bindings.MOCK_GSUITE_USERS[0][
    "users"
]
TEST_POLICY_BINDING_PRINCIPAL_EMAIL = TEST_POLICY_BINDING_GSUITE_USERS[0][
    "primaryEmail"
]
TEST_VIEWER_ROLE = "roles/viewer"
COMMON_JOB_PARAMS = {
    "UPDATE_TAG": TEST_UPDATE_TAG,
    "ORG_RESOURCE_NAME": "organizations/1337",
    "PROJECT_ID": TEST_PROJECT_ID,
}
GSUITE_COMMON_PARAMS = {
    **COMMON_JOB_PARAMS,
    "CUSTOMER_ID": "customer-123",
}
INHERITED_ORG_BINDING_ID = tests.data.gcp.policy_bindings.INHERITED_ORG_BINDING_ID
INHERITED_FOLDER_BINDING_ID = tests.data.gcp.policy_bindings.INHERITED_FOLDER_BINDING_ID
STALE_INHERITED_ORG_BINDING_ID = "old-org-binding"
STALE_INHERITED_FOLDER_BINDING_ID = "old-folder-binding"


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


def _create_test_organization(neo4j_session):
    """Create a test GCP organization node for org-level roles."""
    neo4j_session.run(
        """
        MERGE (org:GCPOrganization{id: $org_id})
        ON CREATE SET org.firstseen = timestamp()
        SET org.lastupdated = $update_tag
        """,
        org_id=COMMON_JOB_PARAMS["ORG_RESOURCE_NAME"],
        update_tag=TEST_UPDATE_TAG,
    )


def _create_test_bucket(neo4j_session):
    """Create a test GCP bucket node to verify APPLIES_TO relationship wiring."""
    neo4j_session.run(
        """
        MERGE (bucket:GCPBucket{id: $bucket_id})
        ON CREATE SET bucket.firstseen = timestamp()
        SET bucket.lastupdated = $update_tag
        """,
        bucket_id="test-bucket",
        update_tag=TEST_UPDATE_TAG,
    )


def _sync_test_resource_hierarchy(neo4j_session):
    with (
        patch.object(
            cartography.intel.gcp.crm.orgs,
            "get_gcp_organizations",
            return_value=tests.data.gcp.crm.GCP_ORGANIZATIONS,
        ),
        patch.object(
            cartography.intel.gcp.crm.folders,
            "get_gcp_folders",
            return_value=tests.data.gcp.crm.GCP_FOLDERS,
        ),
        patch.object(
            cartography.intel.gcp.crm.projects,
            "get_gcp_projects",
            return_value=tests.data.gcp.crm.GCP_PROJECTS,
        ),
    ):
        cartography.intel.gcp.crm.orgs.sync_gcp_organizations(
            neo4j_session,
            TEST_UPDATE_TAG,
            COMMON_JOB_PARAMS,
        )
        folders = cartography.intel.gcp.crm.folders.sync_gcp_folders(
            neo4j_session,
            TEST_UPDATE_TAG,
            COMMON_JOB_PARAMS,
            COMMON_JOB_PARAMS["ORG_RESOURCE_NAME"],
        )
        cartography.intel.gcp.crm.projects.sync_gcp_projects(
            neo4j_session,
            COMMON_JOB_PARAMS["ORG_RESOURCE_NAME"],
            folders,
            TEST_UPDATE_TAG,
            COMMON_JOB_PARAMS,
        )
        return folders


def _sync_test_principal_and_role(neo4j_session):
    viewer_role = [
        role
        for role in tests.data.gcp.policy_bindings.MOCK_IAM_ROLES
        if role["name"] == TEST_VIEWER_ROLE
    ]
    with (
        patch.object(
            cartography.intel.gcp.iam,
            "get_gcp_predefined_roles",
            return_value=viewer_role,
        ),
        patch.object(
            cartography.intel.gcp.iam,
            "get_gcp_org_roles",
            return_value=[],
        ),
        patch.object(
            cartography.intel.gsuite.users,
            "get_all_users",
            return_value=tests.data.gcp.policy_bindings.MOCK_GSUITE_USERS,
        ),
    ):
        cartography.intel.gcp.iam.sync_org_iam(
            neo4j_session,
            MagicMock(),
            COMMON_JOB_PARAMS["ORG_RESOURCE_NAME"],
            TEST_UPDATE_TAG,
            COMMON_JOB_PARAMS,
        )
        cartography.intel.gsuite.users.sync_gsuite_users(
            neo4j_session,
            MagicMock(),
            TEST_UPDATE_TAG,
            GSUITE_COMMON_PARAMS,
        )


def _reset_inherited_policy_binding_test_scope(neo4j_session):
    neo4j_session.run(
        """
        MATCH (n)
        WHERE
            (n:GCPProject AND n.id = $project_id)
            OR (n:GCPOrganization AND n.id = $org_id)
            OR (n:GCPFolder AND n.id = $folder_id)
            OR (n:GCPPrincipal AND n.email = $email)
            OR (n:GCPRole AND n.name = $role)
            OR (n:GCPPolicyBinding AND n.id IN $binding_ids)
        DETACH DELETE n
        """,
        project_id=TEST_PROJECT_ID,
        org_id=COMMON_JOB_PARAMS["ORG_RESOURCE_NAME"],
        folder_id=TEST_FOLDER_ID,
        email=TEST_POLICY_BINDING_PRINCIPAL_EMAIL,
        role=TEST_VIEWER_ROLE,
        binding_ids=[
            INHERITED_ORG_BINDING_ID,
            INHERITED_FOLDER_BINDING_ID,
            STALE_INHERITED_ORG_BINDING_ID,
            STALE_INHERITED_FOLDER_BINDING_ID,
        ],
    )


def _seed_stale_inherited_policy_bindings(neo4j_session):
    neo4j_session.run(
        """
        MATCH (org:GCPOrganization {id: $org_id})
        MATCH (folder:GCPFolder {id: $folder_id})
        MATCH (principal:GCPPrincipal {email: $email})
        MATCH (role:GCPRole {name: $role})
        MERGE (org_binding:GCPPolicyBinding {id: $org_binding_id})
        SET org_binding.lastupdated = $old_update_tag
        MERGE (folder_binding:GCPPolicyBinding {id: $folder_binding_id})
        SET folder_binding.lastupdated = $old_update_tag
        MERGE (org)-[org_resource:RESOURCE]->(org_binding)
        SET org_resource.lastupdated = $old_update_tag
        MERGE (folder)-[folder_resource:RESOURCE]->(folder_binding)
        SET folder_resource.lastupdated = $old_update_tag
        MERGE (principal)-[org_policy:HAS_ALLOW_POLICY]->(org_binding)
        SET org_policy.lastupdated = $old_update_tag
        MERGE (principal)-[folder_policy:HAS_ALLOW_POLICY]->(folder_binding)
        SET folder_policy.lastupdated = $old_update_tag
        MERGE (org_binding)-[org_role:GRANTS_ROLE]->(role)
        SET org_role.lastupdated = $old_update_tag
        MERGE (folder_binding)-[folder_role:GRANTS_ROLE]->(role)
        SET folder_role.lastupdated = $old_update_tag
        MERGE (org_binding)-[org_applies:APPLIES_TO]->(org)
        SET org_applies.lastupdated = $old_update_tag,
            org_applies._sub_resource_label = "GCPOrganization",
            org_applies._sub_resource_id = $org_id
        MERGE (folder_binding)-[folder_applies:APPLIES_TO]->(folder)
        SET folder_applies.lastupdated = $old_update_tag,
            folder_applies._sub_resource_label = "GCPFolder",
            folder_applies._sub_resource_id = $folder_id
        """,
        org_id=COMMON_JOB_PARAMS["ORG_RESOURCE_NAME"],
        folder_id=TEST_FOLDER_ID,
        email=TEST_POLICY_BINDING_PRINCIPAL_EMAIL,
        role=TEST_VIEWER_ROLE,
        old_update_tag=TEST_UPDATE_TAG - 1,
        org_binding_id=STALE_INHERITED_ORG_BINDING_ID,
        folder_binding_id=STALE_INHERITED_FOLDER_BINDING_ID,
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
    "get_gcp_predefined_roles",
    return_value=tests.data.gcp.policy_bindings.MOCK_IAM_ROLES,
)
@patch.object(
    cartography.intel.gcp.iam,
    "get_gcp_org_roles",
    return_value=[],
)
@patch.object(
    cartography.intel.gcp.iam,
    "get_gcp_project_custom_roles",
    return_value=[],
)
@patch.object(
    cartography.intel.gcp.iam,
    "get_gcp_service_accounts",
    return_value=tests.data.gcp.policy_bindings.MOCK_IAM_SERVICE_ACCOUNTS,
)
def test_sync_gcp_policy_bindings(
    mock_get_service_accounts,
    mock_get_project_custom_roles,
    mock_get_org_roles,
    mock_get_predefined_roles,
    mock_get_all_users,
    mock_get_all_groups,
    mock_get_group_members,
    mock_get_policy_bindings,
    neo4j_session,
):
    """
    Test that GCP policy bindings sync creates the expected nodes and relationships.
    """
    # Arrange
    _create_test_project(neo4j_session)
    _create_test_organization(neo4j_session)
    _create_test_bucket(neo4j_session)
    mock_iam_client = MagicMock()
    mock_admin_resource = MagicMock()
    mock_asset_client = MagicMock()

    # Sync org-level IAM (predefined roles) first
    cartography.intel.gcp.iam.sync_org_iam(
        neo4j_session,
        mock_iam_client,
        COMMON_JOB_PARAMS["ORG_RESOURCE_NAME"],
        TEST_UPDATE_TAG,
        COMMON_JOB_PARAMS,
    )

    # Sync project-level IAM (service accounts and project custom roles)
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
    role_permissions_by_name = cartography.intel.gcp.iam.build_role_permissions_by_name(
        tests.data.gcp.policy_bindings.MOCK_IAM_ROLES
    )

    # Act
    cartography.intel.gcp.policy_bindings.sync(
        neo4j_session,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        COMMON_JOB_PARAMS,
        mock_asset_client,
        role_permissions_by_name,
    )

    # Assert
    # Check GCP policy binding nodes
    assert check_nodes(
        neo4j_session, "GCPPolicyBinding", ["id", "role", "resource_type"]
    ) == {
        (
            "//cloudresourcemanager.googleapis.com/projects/project-abc_roles/editor",
            "roles/editor",
            "project",
        ),
        (
            "//cloudresourcemanager.googleapis.com/projects/project-abc_roles/viewer",
            "roles/viewer",
            "project",
        ),
        (
            "//cloudresourcemanager.googleapis.com/projects/project-abc_roles/storage.admin_5982c9d5",
            "roles/storage.admin",
            "project",
        ),
        (
            "//cloudresourcemanager.googleapis.com/projects/project-abc_roles/test.gcp_extended",
            "roles/test.gcp_extended",
            "project",
        ),
        (
            "//cloudresourcemanager.googleapis.com/projects/project-abc_roles/iam.serviceAccountTokenCreator",
            "roles/iam.serviceAccountTokenCreator",
            "project",
        ),
        (
            "//storage.googleapis.com/buckets/test-bucket_roles/storage.objectViewer",
            "roles/storage.objectViewer",
            "resource",
        ),
        (
            "//bigquery.googleapis.com/projects/project-abc/datasets/dataset_a/tables/events_roles/bigquery.dataViewer",
            "roles/bigquery.dataViewer",
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
            "//cloudresourcemanager.googleapis.com/projects/project-abc_roles/editor",
        ),
        (
            TEST_PROJECT_ID,
            "//cloudresourcemanager.googleapis.com/projects/project-abc_roles/viewer",
        ),
        (
            TEST_PROJECT_ID,
            "//cloudresourcemanager.googleapis.com/projects/project-abc_roles/storage.admin_5982c9d5",
        ),
        (
            TEST_PROJECT_ID,
            "//cloudresourcemanager.googleapis.com/projects/project-abc_roles/test.gcp_extended",
        ),
        (
            TEST_PROJECT_ID,
            "//cloudresourcemanager.googleapis.com/projects/project-abc_roles/iam.serviceAccountTokenCreator",
        ),
        (
            TEST_PROJECT_ID,
            "//storage.googleapis.com/buckets/test-bucket_roles/storage.objectViewer",
        ),
        (
            TEST_PROJECT_ID,
            "//bigquery.googleapis.com/projects/project-abc/datasets/dataset_a/tables/events_roles/bigquery.dataViewer",
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
            "//cloudresourcemanager.googleapis.com/projects/project-abc_roles/editor",
        ),
        (
            "alice@example.com",
            "//cloudresourcemanager.googleapis.com/projects/project-abc_roles/test.gcp_extended",
        ),
        (
            "alice@example.com",
            "//storage.googleapis.com/buckets/test-bucket_roles/storage.objectViewer",
        ),
        (
            "bob@example.com",
            "//cloudresourcemanager.googleapis.com/projects/project-abc_roles/storage.admin_5982c9d5",
        ),
        (
            "bob@example.com",
            "//cloudresourcemanager.googleapis.com/projects/project-abc_roles/iam.serviceAccountTokenCreator",
        ),
        (
            "bob@example.com",
            "//bigquery.googleapis.com/projects/project-abc/datasets/dataset_a/tables/events_roles/bigquery.dataViewer",
        ),
        # IAM service account
        (
            "sa@project-abc.iam.gserviceaccount.com",
            "//cloudresourcemanager.googleapis.com/projects/project-abc_roles/editor",
        ),
        # GSuite group
        (
            "viewers@example.com",
            "//cloudresourcemanager.googleapis.com/projects/project-abc_roles/viewer",
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
            "//cloudresourcemanager.googleapis.com/projects/project-abc_roles/editor",
            "roles/editor",
        ),
        (
            "//cloudresourcemanager.googleapis.com/projects/project-abc_roles/viewer",
            "roles/viewer",
        ),
        (
            "//cloudresourcemanager.googleapis.com/projects/project-abc_roles/storage.admin_5982c9d5",
            "roles/storage.admin",
        ),
        (
            "//cloudresourcemanager.googleapis.com/projects/project-abc_roles/test.gcp_extended",
            "roles/test.gcp_extended",
        ),
        (
            "//cloudresourcemanager.googleapis.com/projects/project-abc_roles/iam.serviceAccountTokenCreator",
            "roles/iam.serviceAccountTokenCreator",
        ),
        (
            "//storage.googleapis.com/buckets/test-bucket_roles/storage.objectViewer",
            "roles/storage.objectViewer",
        ),
        (
            "//bigquery.googleapis.com/projects/project-abc/datasets/dataset_a/tables/events_roles/bigquery.dataViewer",
            "roles/bigquery.dataViewer",
        ),
    }

    # Check GCPPolicyBinding to GCPProject APPLIES_TO relationships
    # (only created when the bound resource node already exists in the graph)
    assert check_rels(
        neo4j_session,
        "GCPPolicyBinding",
        "id",
        "GCPProject",
        "id",
        "APPLIES_TO",
        rel_direction_right=True,
    ) == {
        (
            "//cloudresourcemanager.googleapis.com/projects/project-abc_roles/editor",
            TEST_PROJECT_ID,
        ),
        (
            "//cloudresourcemanager.googleapis.com/projects/project-abc_roles/viewer",
            TEST_PROJECT_ID,
        ),
        (
            "//cloudresourcemanager.googleapis.com/projects/project-abc_roles/storage.admin_5982c9d5",
            TEST_PROJECT_ID,
        ),
        (
            "//cloudresourcemanager.googleapis.com/projects/project-abc_roles/test.gcp_extended",
            TEST_PROJECT_ID,
        ),
        (
            "//cloudresourcemanager.googleapis.com/projects/project-abc_roles/iam.serviceAccountTokenCreator",
            TEST_PROJECT_ID,
        ),
    }

    # Check GCPPolicyBinding to GCPBucket APPLIES_TO relationships
    assert check_rels(
        neo4j_session,
        "GCPPolicyBinding",
        "id",
        "GCPBucket",
        "id",
        "APPLIES_TO",
        rel_direction_right=True,
    ) == {
        (
            "//storage.googleapis.com/buckets/test-bucket_roles/storage.objectViewer",
            "test-bucket",
        ),
    }

    # The bucket binding mixes a real principal with allUsers. The binding is
    # persisted with is_public=true; allUsers is intentionally NOT added to
    # the members list (no GCPPrincipal can ever resolve to it).
    bucket_binding = neo4j_session.run(
        """
        MATCH (b:GCPPolicyBinding {id: $binding_id})
        RETURN b.is_public AS is_public, b.members AS members
        """,
        binding_id="//storage.googleapis.com/buckets/test-bucket_roles/storage.objectViewer",
    ).single()
    assert bucket_binding["is_public"] is True
    assert sorted(bucket_binding["members"]) == ["alice@example.com"]


@patch.object(
    cartography.intel.gcp.policy_bindings,
    "get_policy_bindings",
    return_value=tests.data.gcp.policy_bindings.MOCK_INHERITED_POLICY_BINDINGS_RESPONSE,
)
def test_sync_gcp_inherited_policy_bindings_are_owned_by_scope(
    mock_get_policy_bindings,
    neo4j_session,
):
    # Arrange
    _reset_inherited_policy_binding_test_scope(neo4j_session)
    _sync_test_resource_hierarchy(neo4j_session)
    _sync_test_principal_and_role(neo4j_session)

    # Act
    result = cartography.intel.gcp.policy_bindings.sync(
        neo4j_session,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        COMMON_JOB_PARAMS,
        MagicMock(),
        {TEST_VIEWER_ROLE: ["storage.objects.get"]},
    )

    # Assert
    assert (
        result.status
        == cartography.intel.gcp.policy_bindings.PolicyBindingsSyncStatus.SUCCESS
    )
    inherited_nodes = {
        tuple(row)
        for row in neo4j_session.run(
            """
            MATCH (binding:GCPPolicyBinding)
            WHERE binding.id IN $binding_ids
            RETURN binding.id, binding.role, binding.resource_type
            """,
            binding_ids=[INHERITED_ORG_BINDING_ID, INHERITED_FOLDER_BINDING_ID],
        )
    }
    assert inherited_nodes == {
        (
            INHERITED_ORG_BINDING_ID,
            TEST_VIEWER_ROLE,
            "organization",
        ),
        (
            INHERITED_FOLDER_BINDING_ID,
            TEST_VIEWER_ROLE,
            "folder",
        ),
    }
    assert check_rels(
        neo4j_session,
        "GCPOrganization",
        "id",
        "GCPPolicyBinding",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (
            "organizations/1337",
            INHERITED_ORG_BINDING_ID,
        ),
    }
    assert check_rels(
        neo4j_session,
        "GCPFolder",
        "id",
        "GCPPolicyBinding",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (
            TEST_FOLDER_ID,
            INHERITED_FOLDER_BINDING_ID,
        ),
    }
    inherited_project_resource_edges = neo4j_session.run(
        """
        MATCH (:GCPProject)-[:RESOURCE]->(binding:GCPPolicyBinding)
        WHERE binding.id IN $binding_ids
        RETURN count(binding) AS count
        """,
        binding_ids=[INHERITED_ORG_BINDING_ID, INHERITED_FOLDER_BINDING_ID],
    ).single()["count"]
    assert inherited_project_resource_edges == 0
    has_allow_policy_rels = {
        tuple(row)
        for row in neo4j_session.run(
            """
            MATCH (principal:GCPPrincipal)-[:HAS_ALLOW_POLICY]->(
                binding:GCPPolicyBinding
            )
            WHERE binding.id IN $binding_ids
            RETURN principal.email, binding.id
            """,
            binding_ids=[INHERITED_ORG_BINDING_ID, INHERITED_FOLDER_BINDING_ID],
        )
    }
    assert has_allow_policy_rels == {
        (
            TEST_POLICY_BINDING_PRINCIPAL_EMAIL,
            INHERITED_ORG_BINDING_ID,
        ),
        (
            TEST_POLICY_BINDING_PRINCIPAL_EMAIL,
            INHERITED_FOLDER_BINDING_ID,
        ),
    }
    grants_role_rels = {
        tuple(row)
        for row in neo4j_session.run(
            """
            MATCH (binding:GCPPolicyBinding)-[:GRANTS_ROLE]->(role:GCPRole)
            WHERE binding.id IN $binding_ids
            RETURN binding.id, role.name
            """,
            binding_ids=[INHERITED_ORG_BINDING_ID, INHERITED_FOLDER_BINDING_ID],
        )
    }
    assert grants_role_rels == {
        (
            INHERITED_ORG_BINDING_ID,
            TEST_VIEWER_ROLE,
        ),
        (
            INHERITED_FOLDER_BINDING_ID,
            TEST_VIEWER_ROLE,
        ),
    }
    assert check_rels(
        neo4j_session,
        "GCPPolicyBinding",
        "id",
        "GCPOrganization",
        "id",
        "APPLIES_TO",
        rel_direction_right=True,
    ) == {
        (
            INHERITED_ORG_BINDING_ID,
            "organizations/1337",
        ),
    }
    assert check_rels(
        neo4j_session,
        "GCPPolicyBinding",
        "id",
        "GCPFolder",
        "id",
        "APPLIES_TO",
        rel_direction_right=True,
    ) == {
        (
            INHERITED_FOLDER_BINDING_ID,
            TEST_FOLDER_ID,
        ),
    }


def test_cleanup_gcp_inherited_policy_bindings(neo4j_session):
    # Arrange
    _reset_inherited_policy_binding_test_scope(neo4j_session)
    folders = _sync_test_resource_hierarchy(neo4j_session)
    _sync_test_principal_and_role(neo4j_session)
    _seed_stale_inherited_policy_bindings(neo4j_session)

    # Act
    cartography.intel.gcp.policy_bindings.cleanup_inherited_policy_bindings(
        neo4j_session,
        COMMON_JOB_PARAMS,
        [folder["name"] for folder in folders if folder.get("name")],
    )

    # Assert
    stale_nodes = neo4j_session.run(
        """
        MATCH (binding:GCPPolicyBinding)
        WHERE binding.id IN $binding_ids
        RETURN count(binding) AS count
        """,
        binding_ids=[
            STALE_INHERITED_ORG_BINDING_ID,
            STALE_INHERITED_FOLDER_BINDING_ID,
        ],
    ).single()["count"]
    assert stale_nodes == 0


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
    When the user lacks org-level cloudasset.viewer role, sync should return a
    skipped status and not raise an exception.
    """
    # Arrange
    _create_test_project(neo4j_session)
    mock_asset_client = MagicMock()

    # Act
    result = cartography.intel.gcp.policy_bindings.sync(
        neo4j_session,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        COMMON_JOB_PARAMS,
        mock_asset_client,
        {},
    )

    # Assert
    # Sync should return a skipped status and not raise an exception.
    assert (
        result.status
        == cartography.intel.gcp.policy_bindings.PolicyBindingsSyncStatus.SKIPPED_PERMISSION_DENIED
    )
    mock_get_policy_bindings.assert_called_once()
