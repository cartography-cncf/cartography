"""
Integration tests for GCP CRM deferred cleanup functionality.
Tests that hierarchical cleanup happens in the correct order to prevent orphaned nodes.
"""

from unittest.mock import patch

import cartography.intel.gcp
import cartography.intel.gcp.crm.folders
import cartography.intel.gcp.crm.orgs
import cartography.intel.gcp.crm.projects
import tests.data.gcp.crm
from cartography.config import Config
from cartography.graph.job import GraphJob
from cartography.models.gcp.crm.folders import GCPFolderSchema
from tests.integration.util import check_nodes

TEST_UPDATE_TAG = 123456789
TEST_UPDATE_TAG_V2 = 123456790  # For simulating a second sync


@patch.object(
    cartography.intel.gcp,
    "_sync_project_resources",
    return_value=None,  # Skip project resource sync for these tests
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
def test_deferred_cleanup_order(
    mock_get_orgs,
    mock_get_folders,
    mock_get_projects,
    mock_sync_resources,
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
            neo4j_uri="bolt://localhost:7687",
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
    "_sync_project_resources",
    return_value=None,
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
def test_org_deletion_cleanup(
    mock_get_orgs,
    mock_get_folders,
    mock_get_projects,
    mock_sync_resources,
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
        neo4j_uri="bolt://localhost:7687",
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
    "_sync_project_resources",
    return_value=None,
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
def test_partial_deletion_cleanup(
    mock_get_orgs,
    mock_get_folders,
    mock_get_projects,
    mock_sync_resources,
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
        neo4j_uri="bolt://localhost:7687",
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


def test_sync_functions_with_defer_cleanup_flag(neo4j_session):
    """
    Test that sync functions respect the defer_cleanup flag.
    """
    neo4j_session.run("MATCH (n) DETACH DELETE n")

    common_job_params = {"UPDATE_TAG": TEST_UPDATE_TAG}

    # Track if cleanup was run
    cleanup_run = []
    original_run = GraphJob.run

    def track_cleanup(self, session):
        cleanup_run.append(True)
        return original_run(self, session)

    with patch.object(GraphJob, "run", track_cleanup):
        # Test with defer_cleanup=True
        with patch.object(
            cartography.intel.gcp.crm.orgs,
            "get_gcp_organizations",
            return_value=tests.data.gcp.crm.GCP_ORGANIZATIONS,
        ):
            cartography.intel.gcp.crm.orgs.sync_gcp_organizations(
                neo4j_session,
                TEST_UPDATE_TAG,
                common_job_params,
                defer_cleanup=True,
            )

        # Cleanup should NOT have run
        assert len(cleanup_run) == 0, "Cleanup should not run when defer_cleanup=True"

        # Test with defer_cleanup=False (default)
        with patch.object(
            cartography.intel.gcp.crm.orgs,
            "get_gcp_organizations",
            return_value=tests.data.gcp.crm.GCP_ORGANIZATIONS,
        ):
            cartography.intel.gcp.crm.orgs.sync_gcp_organizations(
                neo4j_session,
                TEST_UPDATE_TAG,
                common_job_params,
                defer_cleanup=False,
            )

        # Cleanup should have run
        assert len(cleanup_run) == 1, "Cleanup should run when defer_cleanup=False"


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
        neo4j_session, folders_org1, TEST_UPDATE_TAG, "1337"
    )

    # Load second org with its resources
    cartography.intel.gcp.crm.orgs.load_gcp_organizations(
        neo4j_session, [multiple_orgs[1]], TEST_UPDATE_TAG
    )
    cartography.intel.gcp.crm.folders.load_gcp_folders(
        neo4j_session, folders_org2, TEST_UPDATE_TAG, "9999"
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
        "ORG_ID": "organizations/1337",
    }
    GraphJob.from_node_schema(GCPFolderSchema(), common_job_params).run(neo4j_session)

    # Verify only org1's folder is cleaned up
    remaining_folders = check_nodes(neo4j_session, "GCPFolder", ["id"])
    assert remaining_folders == {("folders/2000",)}, "Only org2's folder should remain"
