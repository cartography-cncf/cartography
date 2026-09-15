"""
Integration tests for GCP CRM deferred cleanup functionality.
Tests that hierarchical cleanup happens in the correct order to prevent orphaned nodes.
"""

from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.gcp
import cartography.intel.gcp.crm.folders
import cartography.intel.gcp.crm.orgs
import cartography.intel.gcp.crm.projects
import cartography.intel.gcp.iam
import tests.data.gcp.crm
import tests.data.gcp.iam
from cartography.config import Config
from cartography.graph.job import GraphJob
from cartography.models.gcp.crm.folders import GCPFolderSchema
from tests.integration import settings
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_UPDATE_TAG_V2 = 123456790  # For simulating a second sync
SKIPPED_PROJECT_RESOURCES_RESULT = cartography.intel.gcp.GCPProjectResourcesSyncResult(
    policy_bindings_cleanup_safe=False,
)


def _make_fake_credentials():
    """Create a mock GCP credentials object for testing."""
    creds = MagicMock()
    creds.quota_project_id = "test-quota-project"
    creds.universe_domain = "googleapis.com"
    return creds


@patch.object(
    cartography.intel.gcp,
    "get_gcp_credentials",
    return_value=_make_fake_credentials(),
)
@patch.object(
    cartography.intel.gcp,
    "_sync_project_resources",
    return_value=SKIPPED_PROJECT_RESOURCES_RESULT,  # Skip project resource sync for these tests
)
@patch.object(
    cartography.intel.gcp.crm.projects,
    "get_gcp_projects",
    return_value=tests.data.gcp.crm.GCP_PROJECTS,
)
@patch.object(
    cartography.intel.gcp.crm.folders,
    "get_gcp_folders",
    return_value=tests.data.gcp.crm.GCP_FOLDERS,
)
@patch.object(
    cartography.intel.gcp.crm.orgs,
    "get_gcp_organizations",
    return_value=tests.data.gcp.crm.GCP_ORGANIZATIONS,
)
@patch.object(
    cartography.intel.gcp.iam,
    "get_gcp_predefined_roles",
    return_value=[],
)
@patch.object(
    cartography.intel.gcp.iam,
    "get_gcp_org_roles",
    return_value=[],
)
def test_deferred_cleanup_order(
    mock_get_org_roles,
    mock_get_predefined_roles,
    mock_get_orgs,
    mock_get_folders,
    mock_get_projects,
    mock_sync_resources,
    mock_get_creds,
    neo4j_session,
):
    """
    Test that cleanup happens in the correct order:
    1. Project resources (immediate)
    2. Projects (deferred, but before folders)
    3. Folders (deferred, but before orgs)
    4. Organizations (last)
    """
    neo4j_session.run("MATCH (n) DETACH DELETE n")

    # Track the order of cleanup job executions
    cleanup_order = []
    original_run = GraphJob.run

    def track_cleanup(self, session):
        # Track which schema is being cleaned up
        if hasattr(self, "name"):
            cleanup_order.append(self.name)
        return original_run(self, session)

    with patch.object(GraphJob, "run", track_cleanup):
        # Create a minimal config
        config = Config(
            neo4j_uri=settings.get("NEO4J_URL"),
            update_tag=TEST_UPDATE_TAG,
        )

        # Run the main GCP ingestion
        cartography.intel.gcp.start_gcp_ingestion(neo4j_session, config)

    # Verify cleanup happened in the correct order
    # Should see: Projects cleaned up before Folders, Folders before Organizations
    # The job names include "Cleanup" prefix
    assert any(
        "GCPProject" in name for name in cleanup_order
    ), f"GCPProject cleanup not found in {cleanup_order}"
    assert any(
        "GCPFolder" in name for name in cleanup_order
    ), f"GCPFolder cleanup not found in {cleanup_order}"
    assert any(
        "GCPOrganization" in name for name in cleanup_order
    ), f"GCPOrganization cleanup not found in {cleanup_order}"

    # Find the indices of cleanup jobs
    project_idx = next(
        i for i, name in enumerate(cleanup_order) if "GCPProject" in name
    )
    folder_idx = next(i for i, name in enumerate(cleanup_order) if "GCPFolder" in name)
    org_idx = next(
        i for i, name in enumerate(cleanup_order) if "GCPOrganization" in name
    )

    assert (
        project_idx < folder_idx
    ), f"Projects should be cleaned before folders: {cleanup_order}"
    assert (
        folder_idx < org_idx
    ), f"Folders should be cleaned before orgs: {cleanup_order}"


@patch.object(
    cartography.intel.gcp,
    "get_gcp_credentials",
    return_value=_make_fake_credentials(),
)
@patch.object(
    cartography.intel.gcp,
    "_sync_project_resources",
    return_value=SKIPPED_PROJECT_RESOURCES_RESULT,
)
@patch.object(
    cartography.intel.gcp.crm.projects,
    "get_gcp_projects",
)
@patch.object(
    cartography.intel.gcp.crm.folders,
    "get_gcp_folders",
)
@patch.object(
    cartography.intel.gcp.crm.orgs,
    "get_gcp_organizations",
)
@patch.object(
    cartography.intel.gcp.iam,
    "get_gcp_predefined_roles",
    return_value=[],
)
@patch.object(
    cartography.intel.gcp.iam,
    "get_gcp_org_roles",
    return_value=[],
)
def test_org_deletion_cleanup(
    mock_get_org_roles,
    mock_get_predefined_roles,
    mock_get_orgs,
    mock_get_folders,
    mock_get_projects,
    mock_sync_resources,
    mock_get_creds,
    neo4j_session,
):
    """
    Test that when an org is deleted (no longer returned by API),
    its projects and folders are cleaned up properly.
    """
    neo4j_session.run("MATCH (n) DETACH DELETE n")

    # First sync: org exists with folders and projects
    mock_get_orgs.return_value = tests.data.gcp.crm.GCP_ORGANIZATIONS
    mock_get_folders.return_value = tests.data.gcp.crm.GCP_FOLDERS
    mock_get_projects.return_value = tests.data.gcp.crm.GCP_PROJECTS

    config = Config(
        neo4j_uri=settings.get("NEO4J_URL"),
        update_tag=TEST_UPDATE_TAG,
    )

    cartography.intel.gcp.start_gcp_ingestion(neo4j_session, config)

    # Verify initial state - org, folders, and projects exist
    assert len(check_nodes(neo4j_session, "GCPOrganization", ["id"])) == 1
    assert len(check_nodes(neo4j_session, "GCPFolder", ["id"])) == 1
    assert len(check_nodes(neo4j_session, "GCPProject", ["id"])) == 1

    # Second sync: org no longer exists (lost access)
    mock_get_orgs.return_value = []  # No orgs returned
    mock_get_folders.return_value = []  # No folders returned
    mock_get_projects.return_value = []  # No projects returned

    config.update_tag = TEST_UPDATE_TAG_V2
    cartography.intel.gcp.start_gcp_ingestion(neo4j_session, config)

    # In the current implementation, when an org is no longer returned by the API,
    # we don't enter the loop to process it, so no cleanup jobs are created for it
    # or its children. Everything becomes stale but remains in the graph.
    # This preserves data in case of temporary access loss.

    # All resources remain but are stale (have old update_tag)
    assert (
        len(check_nodes(neo4j_session, "GCPOrganization", ["id"])) == 1
    ), "Organization remains (stale) when no longer accessible"
    assert (
        len(check_nodes(neo4j_session, "GCPFolder", ["id"])) == 1
    ), "Folders remain (stale) when org not accessible"
    assert (
        len(check_nodes(neo4j_session, "GCPProject", ["id"])) == 1
    ), "Projects remain (stale) when org not accessible"

    # Verify they are stale (have the old update tag)
    orgs_with_tags = check_nodes(
        neo4j_session, "GCPOrganization", ["id", "lastupdated"]
    )
    assert all(
        tag < TEST_UPDATE_TAG_V2 for _, tag in orgs_with_tags
    ), "Org should be stale"


@patch.object(
    cartography.intel.gcp,
    "get_gcp_credentials",
    return_value=_make_fake_credentials(),
)
@patch.object(
    cartography.intel.gcp,
    "_sync_project_resources",
    return_value=SKIPPED_PROJECT_RESOURCES_RESULT,
)
@patch.object(
    cartography.intel.gcp.crm.projects,
    "get_gcp_projects",
)
@patch.object(
    cartography.intel.gcp.crm.folders,
    "get_gcp_folders",
)
@patch.object(
    cartography.intel.gcp.crm.orgs,
    "get_gcp_organizations",
)
@patch.object(
    cartography.intel.gcp.iam,
    "get_gcp_predefined_roles",
    return_value=[],
)
@patch.object(
    cartography.intel.gcp.iam,
    "get_gcp_org_roles",
    return_value=[],
)
def test_partial_deletion_cleanup(
    mock_get_org_roles,
    mock_get_predefined_roles,
    mock_get_orgs,
    mock_get_folders,
    mock_get_projects,
    mock_sync_resources,
    mock_get_creds,
    neo4j_session,
):
    """
    Test that when some resources are deleted but not others,
    cleanup works correctly.
    """
    neo4j_session.run("MATCH (n) DETACH DELETE n")

    # First sync: org exists with folders and projects
    mock_get_orgs.return_value = tests.data.gcp.crm.GCP_ORGANIZATIONS
    mock_get_folders.return_value = tests.data.gcp.crm.GCP_FOLDERS
    mock_get_projects.return_value = tests.data.gcp.crm.GCP_PROJECTS

    config = Config(
        neo4j_uri=settings.get("NEO4J_URL"),
        update_tag=TEST_UPDATE_TAG,
    )

    cartography.intel.gcp.start_gcp_ingestion(neo4j_session, config)

    # Second sync: org still exists, but folders and projects are gone
    mock_get_orgs.return_value = tests.data.gcp.crm.GCP_ORGANIZATIONS
    mock_get_folders.return_value = []  # No folders
    mock_get_projects.return_value = []  # No projects

    config.update_tag = TEST_UPDATE_TAG_V2
    cartography.intel.gcp.start_gcp_ingestion(neo4j_session, config)

    # Verify org still exists
    assert (
        len(check_nodes(neo4j_session, "GCPOrganization", ["id"])) == 1
    ), "Organization should still exist"

    # Verify folders and projects are cleaned up
    assert (
        len(check_nodes(neo4j_session, "GCPFolder", ["id"])) == 0
    ), "Folders should be cleaned up"
    assert (
        len(check_nodes(neo4j_session, "GCPProject", ["id"])) == 0
    ), "Projects should be cleaned up"


@patch.object(
    cartography.intel.gcp,
    "get_gcp_credentials",
    return_value=_make_fake_credentials(),
)
@patch.object(
    cartography.intel.gcp,
    "_sync_project_resources",
    return_value=SKIPPED_PROJECT_RESOURCES_RESULT,  # Skip project resource sync for these tests
)
@patch.object(
    cartography.intel.gcp.iam,
    "get_gcp_predefined_roles",
    return_value=[],
)
@patch.object(
    cartography.intel.gcp.iam,
    "get_gcp_org_roles",
    return_value=[],
)
def test_project_migration_between_orgs(
    mock_get_org_roles,
    mock_get_predefined_roles,
    mock_sync_resources,
    mock_get_creds,
    neo4j_session,
):
    """
    Test that when a project migrates from one org to another,
    old relationships are properly cleaned up using the full ingestion flow.
    """
    neo4j_session.run("MATCH (n) DETACH DELETE n")

    # Two organizations
    orgs_initial = [
        {
            "name": "organizations/1337",
            "displayName": "org1.com",
            "lifecycleState": "ACTIVE",
        },
        {
            "name": "organizations/9999",
            "displayName": "org2.com",
            "lifecycleState": "ACTIVE",
        },
    ]

    # Project initially under org1
    projects_org1_initial = [
        {
            "projectId": "migrating-project",
            "projectNumber": "123456",
            "name": "Migrating Project",
            "lifecycleState": "ACTIVE",
            "parent": "organizations/1337",
        },
    ]
    projects_org2_initial = []  # No projects in org2 initially

    # Mock data for first sync
    def get_projects_initial(
        org_resource_name,
        folders,
        credentials=None,
        exclude_org_root_projects=False,
    ):
        if org_resource_name == "organizations/1337":
            return projects_org1_initial
        elif org_resource_name == "organizations/9999":
            return projects_org2_initial
        return []

    # First sync: project belongs to org1
    with (
        patch.object(
            cartography.intel.gcp.crm.orgs,
            "get_gcp_organizations",
            return_value=orgs_initial,
        ),
        patch.object(
            cartography.intel.gcp.crm.folders,
            "get_gcp_folders",
            return_value=[],  # No folders for simplicity
        ),
        patch.object(
            cartography.intel.gcp.crm.projects,
            "get_gcp_projects",
            side_effect=get_projects_initial,
        ),
    ):
        config = Config(
            neo4j_uri=settings.get("NEO4J_URL"),
            update_tag=TEST_UPDATE_TAG,
        )
        cartography.intel.gcp.start_gcp_ingestion(neo4j_session, config)

    # Verify initial state
    parent_rels = check_rels(
        neo4j_session,
        "GCPProject",
        "id",
        "GCPOrganization",
        "id",
        "PARENT",
        rel_direction_right=True,
    )
    assert parent_rels == {
        ("migrating-project", "organizations/1337"),
    }, "Project should have PARENT relationship to org1"

    resource_rels = check_rels(
        neo4j_session,
        "GCPOrganization",
        "id",
        "GCPProject",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    )
    assert resource_rels == {
        ("organizations/1337", "migrating-project"),
    }, "Org1 should have RESOURCE relationship to project"

    # Project migrates to org2
    projects_org1_after = []  # Project no longer in org1
    projects_org2_after = [
        {
            "projectId": "migrating-project",
            "projectNumber": "123456",
            "name": "Migrating Project",
            "lifecycleState": "ACTIVE",
            "parent": "organizations/9999",  # Now under org2
        },
    ]

    # Mock data for second sync
    def get_projects_after_migration(
        org_resource_name,
        folders,
        credentials=None,
        exclude_org_root_projects=False,
    ):
        if org_resource_name == "organizations/1337":
            return projects_org1_after
        elif org_resource_name == "organizations/9999":
            return projects_org2_after
        return []

    # Second sync: project now belongs to org2
    with (
        patch.object(
            cartography.intel.gcp.crm.orgs,
            "get_gcp_organizations",
            return_value=orgs_initial,  # Same orgs
        ),
        patch.object(
            cartography.intel.gcp.crm.folders,
            "get_gcp_folders",
            return_value=[],  # No folders
        ),
        patch.object(
            cartography.intel.gcp.crm.projects,
            "get_gcp_projects",
            side_effect=get_projects_after_migration,
        ),
    ):
        config = Config(
            neo4j_uri=settings.get("NEO4J_URL"),
            update_tag=TEST_UPDATE_TAG_V2,
        )
        cartography.intel.gcp.start_gcp_ingestion(neo4j_session, config)

    # Verify final state - project should only be related to org2 now
    parent_rels_after = check_rels(
        neo4j_session,
        "GCPProject",
        "id",
        "GCPOrganization",
        "id",
        "PARENT",
        rel_direction_right=True,
    )
    assert parent_rels_after == {
        ("migrating-project", "organizations/9999"),
    }, f"Project should only have PARENT relationship to org2, but got {parent_rels_after}"

    # Check RESOURCE relationships
    resource_rels_after = check_rels(
        neo4j_session,
        "GCPOrganization",
        "id",
        "GCPProject",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    )
    assert resource_rels_after == {
        ("organizations/9999", "migrating-project"),
    }, f"Only org2 should have RESOURCE relationship, but got {resource_rels_after}"


def test_cleanup_with_multiple_orgs(neo4j_session):
    """
    Test that cleanup works correctly when there are multiple organizations.
    """
    neo4j_session.run("MATCH (n) DETACH DELETE n")

    # Create test data with multiple orgs
    multiple_orgs = [
        {
            "name": "organizations/1337",
            "displayName": "example.com",
            "lifecycleState": "ACTIVE",
        },
        {
            "name": "organizations/9999",
            "displayName": "another.com",
            "lifecycleState": "ACTIVE",
        },
    ]

    # Create folders for each org
    folders_org1 = [
        {
            "name": "folders/1000",
            "parent": "organizations/1337",
            "displayName": "folder1",
            "lifecycleState": "ACTIVE",
        },
    ]
    folders_org2 = [
        {
            "name": "folders/2000",
            "parent": "organizations/9999",
            "displayName": "folder2",
            "lifecycleState": "ACTIVE",
        },
    ]

    # Load first org with its resources
    cartography.intel.gcp.crm.orgs.load_gcp_organizations(
        neo4j_session, [multiple_orgs[0]], TEST_UPDATE_TAG
    )
    cartography.intel.gcp.crm.folders.load_gcp_folders(
        neo4j_session, folders_org1, TEST_UPDATE_TAG, "organizations/1337"
    )

    # Load second org with its resources
    cartography.intel.gcp.crm.orgs.load_gcp_organizations(
        neo4j_session, [multiple_orgs[1]], TEST_UPDATE_TAG
    )
    cartography.intel.gcp.crm.folders.load_gcp_folders(
        neo4j_session, folders_org2, TEST_UPDATE_TAG, "organizations/9999"
    )

    # Verify both orgs and their folders exist
    assert (
        len(check_nodes(neo4j_session, "GCPOrganization", ["id"])) == 2
    ), "Should have 2 organizations"
    assert (
        len(check_nodes(neo4j_session, "GCPFolder", ["id"])) == 2
    ), "Should have 2 folders"

    # Run cleanup for org1
    common_job_params = {
        "UPDATE_TAG": TEST_UPDATE_TAG_V2,
        "ORG_RESOURCE_NAME": "organizations/1337",
    }
    GraphJob.from_node_schema(GCPFolderSchema(), common_job_params).run(neo4j_session)

    # Verify only org1's folder is cleaned up
    remaining_folders = check_nodes(neo4j_session, "GCPFolder", ["id"])
    assert remaining_folders == {("folders/2000",)}, "Only org2's folder should remain"


@patch.object(
    cartography.intel.gcp,
    "get_gcp_credentials",
    return_value=_make_fake_credentials(),
)
@patch.object(
    cartography.intel.gcp,
    "_sync_project_resources",
    return_value=SKIPPED_PROJECT_RESOURCES_RESULT,
)
@patch.object(
    cartography.intel.gcp.crm.projects,
    "get_gcp_projects",
)
@patch.object(
    cartography.intel.gcp.crm.folders,
    "get_gcp_folders",
)
@patch.object(
    cartography.intel.gcp.crm.orgs,
    "get_gcp_organizations",
)
@patch.object(
    cartography.intel.gcp.iam,
    "get_gcp_predefined_roles",
    return_value=[],
)
@patch.object(
    cartography.intel.gcp.iam,
    "get_gcp_org_roles",
    return_value=[],
)
def test_excluded_org_is_preserved(
    mock_get_org_roles,
    mock_get_predefined_roles,
    mock_get_orgs,
    mock_get_folders,
    mock_get_projects,
    mock_sync_resources,
    mock_get_creds,
    neo4j_session,
):
    """
    Two-sync coverage: an org added to --gcp-excluded-org-ids after being
    synced was never inventoried in the second run, so its existing data must
    be preserved (stale), not deleted. Callers that want deletion can remove
    the data explicitly.
    """
    neo4j_session.run("MATCH (n) DETACH DELETE n")

    two_orgs = [
        {
            "name": "organizations/1337",
            "displayName": "example.com",
            "lifecycleState": "ACTIVE",
        },
        {
            "name": "organizations/9999",
            "displayName": "another.com",
            "lifecycleState": "ACTIVE",
        },
    ]
    folders_by_org = {
        "organizations/1337": [
            {
                "name": "folders/1000",
                "parent": "organizations/1337",
                "displayName": "folder1",
                "lifecycleState": "ACTIVE",
            },
        ],
        "organizations/9999": [
            {
                "name": "folders/2000",
                "parent": "organizations/9999",
                "displayName": "folder2",
                "lifecycleState": "ACTIVE",
            },
        ],
    }
    projects_by_org = {
        "organizations/1337": [
            {
                "createTime": "2021-01-01T00:00:00Z",
                "lifecycleState": "ACTIVE",
                "name": "org1-project",
                "parent": "folders/1000",
                "projectId": "project-org1",
                "projectNumber": "111111111111",
            },
        ],
        "organizations/9999": [
            {
                "createTime": "2021-01-01T00:00:00Z",
                "lifecycleState": "ACTIVE",
                "name": "org2-project",
                "parent": "folders/2000",
                "projectId": "project-org2",
                "projectNumber": "222222222222",
            },
        ],
    }

    mock_get_orgs.side_effect = lambda credentials=None, excluded_org_ids=None: [
        o
        for o in two_orgs
        if o["name"].split("/")[-1] not in (excluded_org_ids or set())
    ]
    mock_get_folders.side_effect = lambda org_resource_name, credentials=None, excluded_folder_ids=None: folders_by_org[
        org_resource_name
    ]
    mock_get_projects.side_effect = lambda org_resource_name, folders, credentials=None, exclude_org_root_projects=False: projects_by_org[
        org_resource_name
    ]

    # First sync: both orgs ingested.
    config = Config(
        neo4j_uri=settings.get("NEO4J_URL"),
        update_tag=TEST_UPDATE_TAG,
    )
    cartography.intel.gcp.start_gcp_ingestion(neo4j_session, config)

    assert check_nodes(neo4j_session, "GCPOrganization", ["id"]) == {
        ("organizations/1337",),
        ("organizations/9999",),
    }
    assert check_nodes(neo4j_session, "GCPFolder", ["id"]) == {
        ("folders/1000",),
        ("folders/2000",),
    }
    assert check_nodes(neo4j_session, "GCPProject", ["id"]) == {
        ("project-org1",),
        ("project-org2",),
    }

    # Second sync: org 1337 is now excluded.
    config = Config(
        neo4j_uri=settings.get("NEO4J_URL"),
        update_tag=TEST_UPDATE_TAG_V2,
        gcp_excluded_org_ids=["1337"],
    )
    cartography.intel.gcp.start_gcp_ingestion(neo4j_session, config)

    assert check_nodes(neo4j_session, "GCPOrganization", ["id"]) == {
        ("organizations/1337",),
        ("organizations/9999",),
    }, "Excluded org must be preserved, not pruned"
    assert check_nodes(neo4j_session, "GCPFolder", ["id"]) == {
        ("folders/1000",),
        ("folders/2000",),
    }, "Excluded org's folders must be preserved"
    assert check_nodes(neo4j_session, "GCPProject", ["id"]) == {
        ("project-org1",),
        ("project-org2",),
    }, "Excluded org's projects must be preserved"

    # The excluded org's data is stale; the retained org's data is fresh.
    org_tags = dict(
        check_nodes(neo4j_session, "GCPOrganization", ["id", "lastupdated"])
    )
    assert org_tags["organizations/1337"] == TEST_UPDATE_TAG
    assert org_tags["organizations/9999"] == TEST_UPDATE_TAG_V2
    project_tags = dict(check_nodes(neo4j_session, "GCPProject", ["id", "lastupdated"]))
    assert project_tags["project-org1"] == TEST_UPDATE_TAG
    assert project_tags["project-org2"] == TEST_UPDATE_TAG_V2


@patch.object(
    cartography.intel.gcp,
    "get_gcp_credentials",
    return_value=_make_fake_credentials(),
)
@patch.object(
    cartography.intel.gcp,
    "_sync_project_resources",
    return_value=SKIPPED_PROJECT_RESOURCES_RESULT,
)
@patch.object(
    cartography.intel.gcp.crm.projects,
    "get_gcp_projects",
)
@patch.object(
    cartography.intel.gcp.crm.folders,
    "get_gcp_folders",
)
@patch.object(
    cartography.intel.gcp.crm.orgs,
    "get_gcp_organizations",
)
@patch.object(
    cartography.intel.gcp.iam,
    "get_gcp_predefined_roles",
    return_value=tests.data.gcp.iam.LIST_PREDEFINED_ROLES_RESPONSE["roles"],
)
@patch.object(
    cartography.intel.gcp.iam,
    "get_gcp_org_roles",
)
def test_excluded_org_preserves_custom_and_shared_roles(
    mock_get_org_roles,
    mock_get_predefined_roles,
    mock_get_orgs,
    mock_get_folders,
    mock_get_projects,
    mock_sync_resources,
    mock_get_creds,
    neo4j_session,
):
    """
    Two-sync coverage with IAM roles: predefined GCPRole nodes
    (roles/owner, roles/viewer, ...) are shared by every org via RESOURCE
    edges. Excluding one org must leave its own custom roles AND the shared
    predefined roles (and the retained org's relationships to them) intact.
    """
    neo4j_session.run("MATCH (n) DETACH DELETE n")

    two_orgs = [
        {
            "name": "organizations/1337",
            "displayName": "example.com",
            "lifecycleState": "ACTIVE",
        },
        {
            "name": "organizations/9999",
            "displayName": "another.com",
            "lifecycleState": "ACTIVE",
        },
    ]
    custom_roles_by_org = {
        "organizations/1337": [
            {
                "name": "organizations/1337/roles/customRole1",
                "title": "Custom Role 1",
                "includedPermissions": ["resourcemanager.projects.get"],
                "etag": "etag_1",
                "deleted": False,
            },
        ],
        "organizations/9999": [
            {
                "name": "organizations/9999/roles/customRole2",
                "title": "Custom Role 2",
                "includedPermissions": ["resourcemanager.projects.get"],
                "etag": "etag_2",
                "deleted": False,
            },
        ],
    }

    mock_get_orgs.side_effect = lambda credentials=None, excluded_org_ids=None: [
        o
        for o in two_orgs
        if o["name"].split("/")[-1] not in (excluded_org_ids or set())
    ]
    mock_get_org_roles.side_effect = (
        lambda iam_client, org_id, **kwargs: custom_roles_by_org[org_id]
    )
    mock_get_folders.return_value = []
    mock_get_projects.return_value = []

    # First sync: both orgs ingest the same predefined roles.
    config = Config(
        neo4j_uri=settings.get("NEO4J_URL"),
        update_tag=TEST_UPDATE_TAG,
    )
    cartography.intel.gcp.start_gcp_ingestion(neo4j_session, config)

    predefined_role_ids = {
        role["name"]
        for role in tests.data.gcp.iam.LIST_PREDEFINED_ROLES_RESPONSE["roles"]
    }
    roles_before = {
        role_id for (role_id,) in check_nodes(neo4j_session, "GCPRole", ["id"])
    }
    assert predefined_role_ids <= roles_before
    assert "organizations/1337/roles/customRole1" in roles_before
    assert "organizations/9999/roles/customRole2" in roles_before

    # Second sync: org 1337 is excluded.
    config = Config(
        neo4j_uri=settings.get("NEO4J_URL"),
        update_tag=TEST_UPDATE_TAG_V2,
        gcp_excluded_org_ids=["1337"],
    )
    cartography.intel.gcp.start_gcp_ingestion(neo4j_session, config)

    assert check_nodes(neo4j_session, "GCPOrganization", ["id"]) == {
        ("organizations/1337",),
        ("organizations/9999",),
    }, "Excluded org must be preserved"

    roles_after = {
        role_id for (role_id,) in check_nodes(neo4j_session, "GCPRole", ["id"])
    }
    assert predefined_role_ids <= roles_after, "Shared predefined roles must survive"
    assert (
        "organizations/1337/roles/customRole1" in roles_after
    ), "Excluded org's custom role must be preserved (stale), not deleted"
    assert (
        "organizations/9999/roles/customRole2" in roles_after
    ), "Retained org's custom role must survive"

    # Both orgs keep their RESOURCE relationships to the shared roles.
    org_role_rels = check_rels(
        neo4j_session,
        "GCPOrganization",
        "id",
        "GCPRole",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    )
    assert ("organizations/9999", "roles/viewer") in org_role_rels
    assert ("organizations/1337", "roles/viewer") in org_role_rels


ORG_ROOT_PROJECT = {
    "createTime": "2021-01-01T00:00:00Z",
    "lifecycleState": "ACTIVE",
    "name": "org-root-project",
    "parent": "organizations/1337",
    "projectId": "project-org-root",
    "projectNumber": "111111111111",
}

FOLDER_PROJECT = {
    "createTime": "2021-01-01T00:00:00Z",
    "lifecycleState": "ACTIVE",
    "name": "folder-project",
    "parent": "folders/1414",
    "projectId": "project-in-folder",
    "projectNumber": "222222222222",
}

NESTED_FOLDER_PROJECT = {
    "createTime": "2021-01-01T00:00:00Z",
    "lifecycleState": "ACTIVE",
    "name": "nested-folder-project",
    "parent": "folders/2001",
    "projectId": "project-in-nested-folder",
    "projectNumber": "444444444444",
}


@patch.object(
    cartography.intel.gcp,
    "get_gcp_credentials",
    return_value=_make_fake_credentials(),
)
@patch.object(
    cartography.intel.gcp,
    "_sync_project_resources",
    return_value=SKIPPED_PROJECT_RESOURCES_RESULT,
)
@patch.object(
    cartography.intel.gcp.crm.projects,
    "get_gcp_projects",
)
@patch.object(
    cartography.intel.gcp.crm.folders,
    "get_gcp_folders",
    return_value=tests.data.gcp.crm.GCP_FOLDERS,
)
@patch.object(
    cartography.intel.gcp.crm.orgs,
    "get_gcp_organizations",
    return_value=tests.data.gcp.crm.GCP_ORGANIZATIONS,
)
@patch.object(
    cartography.intel.gcp.iam,
    "get_gcp_predefined_roles",
    return_value=[],
)
@patch.object(
    cartography.intel.gcp.iam,
    "get_gcp_org_roles",
    return_value=[],
)
def test_excluded_org_root_projects_are_preserved(
    mock_get_org_roles,
    mock_get_predefined_roles,
    mock_get_orgs,
    mock_get_folders,
    mock_get_projects,
    mock_sync_resources,
    mock_get_creds,
    neo4j_session,
):
    """
    Org-root projects must survive enabling the exclusion: they were synced
    before, are intentionally not listed now, and must not be deleted as stale.
    """
    neo4j_session.run("MATCH (n) DETACH DELETE n")

    projects = [ORG_ROOT_PROJECT, FOLDER_PROJECT]

    def get_projects_respecting_exclusion(
        org_resource_name,
        folders,
        credentials=None,
        exclude_org_root_projects=False,
    ):
        if exclude_org_root_projects:
            return [p for p in projects if p["parent"].startswith("folders")]
        return projects

    mock_get_projects.side_effect = get_projects_respecting_exclusion

    # First sync: org-root projects included.
    config = Config(
        neo4j_uri=settings.get("NEO4J_URL"),
        update_tag=TEST_UPDATE_TAG,
        gcp_exclude_org_root_projects=False,
    )
    cartography.intel.gcp.start_gcp_ingestion(neo4j_session, config)

    assert check_nodes(neo4j_session, "GCPProject", ["id"]) == {
        ("project-org-root",),
        ("project-in-folder",),
    }

    # Second sync: org-root projects excluded.
    config = Config(
        neo4j_uri=settings.get("NEO4J_URL"),
        update_tag=TEST_UPDATE_TAG_V2,
        gcp_exclude_org_root_projects=True,
    )
    cartography.intel.gcp.start_gcp_ingestion(neo4j_session, config)

    assert check_nodes(neo4j_session, "GCPProject", ["id"]) == {
        ("project-org-root",),
        ("project-in-folder",),
    }, "Excluded org-root project must be preserved, not deleted as stale"

    # The excluded project is stale; the included one is fresh.
    project_tags = dict(check_nodes(neo4j_session, "GCPProject", ["id", "lastupdated"]))
    assert project_tags["project-org-root"] == TEST_UPDATE_TAG
    assert project_tags["project-in-folder"] == TEST_UPDATE_TAG_V2


@patch.object(
    cartography.intel.gcp,
    "get_gcp_credentials",
    return_value=_make_fake_credentials(),
)
@patch.object(
    cartography.intel.gcp,
    "_sync_project_resources",
    return_value=SKIPPED_PROJECT_RESOURCES_RESULT,
)
@patch.object(
    cartography.intel.gcp.crm.projects,
    "get_gcp_projects",
)
@patch.object(
    cartography.intel.gcp.crm.folders,
    "get_gcp_folders",
)
@patch.object(
    cartography.intel.gcp.crm.orgs,
    "get_gcp_organizations",
    return_value=tests.data.gcp.crm.GCP_ORGANIZATIONS,
)
@patch.object(
    cartography.intel.gcp.iam,
    "get_gcp_predefined_roles",
    return_value=[],
)
@patch.object(
    cartography.intel.gcp.iam,
    "get_gcp_org_roles",
    return_value=[],
)
def test_excluded_folder_subtree_is_preserved(
    mock_get_org_roles,
    mock_get_predefined_roles,
    mock_get_orgs,
    mock_get_folders,
    mock_get_projects,
    mock_sync_resources,
    mock_get_creds,
    neo4j_session,
):
    """
    Excluding a folder prunes its whole subtree from ingestion; the previously
    synced folders and projects under it must be preserved, not deleted.
    """
    neo4j_session.run("MATCH (n) DETACH DELETE n")

    # First sync: nested folders folders/2000 -> folders/2001, with a project
    # under folders/2001.
    mock_get_folders.return_value = tests.data.gcp.crm.GCP_NESTED_FOLDERS
    mock_get_projects.return_value = [NESTED_FOLDER_PROJECT]

    config = Config(
        neo4j_uri=settings.get("NEO4J_URL"),
        update_tag=TEST_UPDATE_TAG,
    )
    cartography.intel.gcp.start_gcp_ingestion(neo4j_session, config)

    assert check_nodes(neo4j_session, "GCPFolder", ["id"]) == {
        ("folders/2000",),
        ("folders/2001",),
    }
    assert check_nodes(neo4j_session, "GCPProject", ["id"]) == {
        ("project-in-nested-folder",),
    }

    # Second sync: folders/2000 is excluded, so nothing under it is listed.
    def get_folders_respecting_exclusion(
        org_resource_name,
        credentials=None,
        excluded_folder_ids=None,
    ):
        excluded = excluded_folder_ids or set()
        return [
            f
            for f in tests.data.gcp.crm.GCP_NESTED_FOLDERS
            if f["name"].split("/")[-1] not in excluded
            and f["parent"].split("/")[-1] not in excluded
        ]

    mock_get_folders.side_effect = get_folders_respecting_exclusion
    mock_get_projects.return_value = []

    config = Config(
        neo4j_uri=settings.get("NEO4J_URL"),
        update_tag=TEST_UPDATE_TAG_V2,
        gcp_excluded_folder_ids=["2000"],
    )
    cartography.intel.gcp.start_gcp_ingestion(neo4j_session, config)

    assert check_nodes(neo4j_session, "GCPFolder", ["id"]) == {
        ("folders/2000",),
        ("folders/2001",),
    }, "Excluded folder and its subtree must be preserved"
    assert check_nodes(neo4j_session, "GCPProject", ["id"]) == {
        ("project-in-nested-folder",),
    }, "Project under an excluded folder must be preserved"


@patch.object(
    cartography.intel.gcp,
    "get_gcp_credentials",
    return_value=_make_fake_credentials(),
)
@patch.object(
    cartography.intel.gcp,
    "_sync_project_resources",
    return_value=SKIPPED_PROJECT_RESOURCES_RESULT,
)
@patch.object(
    cartography.intel.gcp.crm.projects,
    "get_gcp_projects",
)
@patch.object(
    cartography.intel.gcp.crm.folders,
    "get_gcp_folders",
    return_value=tests.data.gcp.crm.GCP_FOLDERS,
)
@patch.object(
    cartography.intel.gcp.crm.orgs,
    "get_gcp_organizations",
    return_value=tests.data.gcp.crm.GCP_ORGANIZATIONS,
)
@patch.object(
    cartography.intel.gcp.iam,
    "get_gcp_predefined_roles",
    return_value=[],
)
@patch.object(
    cartography.intel.gcp.iam,
    "get_gcp_org_roles",
    return_value=[],
)
def test_resources_moved_into_excluded_folder_are_preserved(
    mock_get_org_roles,
    mock_get_predefined_roles,
    mock_get_orgs,
    mock_get_folders,
    mock_get_projects,
    mock_sync_resources,
    mock_get_creds,
    neo4j_session,
):
    """Cleanup must not delete resources that moved into an excluded subtree."""
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    mock_get_projects.return_value = [FOLDER_PROJECT]
    config = Config(
        neo4j_uri=settings.get("NEO4J_URL"),
        update_tag=TEST_UPDATE_TAG,
    )

    # Act: first sync with the folder and project in the included inventory.
    cartography.intel.gcp.start_gcp_ingestion(neo4j_session, config)

    # Arrange: both resources moved under excluded folder 9999, so neither
    # appears in the partial inventory. Their stored parents still show the old
    # included scope and cannot be used to decide whether they were deleted.
    mock_get_folders.return_value = []
    mock_get_projects.return_value = []

    config = Config(
        neo4j_uri=settings.get("NEO4J_URL"),
        update_tag=TEST_UPDATE_TAG_V2,
        gcp_excluded_folder_ids=["9999"],
    )

    # Act
    cartography.intel.gcp.start_gcp_ingestion(neo4j_session, config)

    # Assert
    assert check_nodes(neo4j_session, "GCPProject", ["id"]) == {
        ("project-in-folder",),
    }
    assert check_nodes(neo4j_session, "GCPFolder", ["id"]) == {
        (folder["name"],) for folder in tests.data.gcp.crm.GCP_FOLDERS
    }
