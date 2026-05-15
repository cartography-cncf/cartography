from unittest.mock import patch

import cartography.intel.gcp.crm
import tests.data.gcp.crm
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
COMMON_JOB_PARAMS = {
    "UPDATE_TAG": TEST_UPDATE_TAG,
    "ORG_RESOURCE_NAME": "organizations/1337",
}


@patch.object(
    cartography.intel.gcp.crm.orgs,
    "get_gcp_organizations",
    return_value=tests.data.gcp.crm.GCP_ORGANIZATIONS,
)
@patch.object(
    cartography.intel.gcp.crm.folders,
    "get_gcp_folders",
    return_value=tests.data.gcp.crm.GCP_FOLDERS,
)
@patch.object(
    cartography.intel.gcp.crm.projects,
    "get_gcp_projects",
    return_value=tests.data.gcp.crm.GCP_PROJECTS,
)
def test_sync_gcp_projects(
    _mock_get_projects, _mock_get_folders, _mock_get_orgs, neo4j_session
) -> None:
    """Test sync_gcp_projects creates project nodes with relationships to folders and org."""
    neo4j_session.run("MATCH (n) DETACH DELETE n")

    # Sync org first
    cartography.intel.gcp.crm.orgs.sync_gcp_organizations(
        neo4j_session, TEST_UPDATE_TAG, COMMON_JOB_PARAMS
    )

    # Sync folders
    folders = cartography.intel.gcp.crm.folders.sync_gcp_folders(
        neo4j_session,
        TEST_UPDATE_TAG,
        COMMON_JOB_PARAMS,
        org_resource_name="organizations/1337",
    )

    # Sync projects
    cartography.intel.gcp.crm.projects.sync_gcp_projects(
        neo4j_session,
        "organizations/1337",
        folders,
        TEST_UPDATE_TAG,
        COMMON_JOB_PARAMS,
    )

    # Verify project nodes
    assert check_nodes(neo4j_session, "GCPProject", ["id"]) == {("project-abc",)}

    # Verify project -> folder PARENT relationship
    assert check_rels(
        neo4j_session,
        "GCPProject",
        "id",
        "GCPFolder",
        "id",
        "PARENT",
        rel_direction_right=True,
    ) == {("project-abc", "folders/1414")}

    # Verify folder -> org PARENT relationship (validates hierarchy)
    assert check_rels(
        neo4j_session,
        "GCPFolder",
        "id",
        "GCPOrganization",
        "id",
        "PARENT",
        rel_direction_right=True,
    ) == {("folders/1414", "organizations/1337")}


@patch.object(
    cartography.intel.gcp.crm.orgs,
    "get_gcp_organizations",
    return_value=tests.data.gcp.crm.GCP_ORGANIZATIONS,
)
@patch.object(
    cartography.intel.gcp.crm.projects,
    "get_gcp_projects",
    return_value=tests.data.gcp.crm.GCP_PROJECTS_WITHOUT_PARENT,
)
def test_sync_gcp_projects_without_parent(
    _mock_get_projects, _mock_get_orgs, neo4j_session
) -> None:
    """Test sync_gcp_projects handles projects without folder parent correctly."""
    neo4j_session.run("MATCH (n) DETACH DELETE n")

    # Sync org first
    cartography.intel.gcp.crm.orgs.sync_gcp_organizations(
        neo4j_session, TEST_UPDATE_TAG, COMMON_JOB_PARAMS
    )

    # Sync projects with no folders
    cartography.intel.gcp.crm.projects.sync_gcp_projects(
        neo4j_session,
        "organizations/1337",
        [],  # No folders
        TEST_UPDATE_TAG,
        COMMON_JOB_PARAMS,
    )

    # Verify project nodes
    assert check_nodes(neo4j_session, "GCPProject", ["id"]) == {("project-abc",)}

    # Verify no project -> folder PARENT relationship
    assert (
        check_rels(
            neo4j_session,
            "GCPProject",
            "id",
            "GCPFolder",
            "id",
            "PARENT",
            rel_direction_right=True,
        )
        == set()
    )


@patch.object(
    cartography.intel.gcp.crm.orgs,
    "get_gcp_organizations",
    return_value=tests.data.gcp.crm.GCP_ORGANIZATIONS,
)
@patch.object(
    cartography.intel.gcp.crm.projects,
    "get_gcp_projects",
    return_value=tests.data.gcp.crm.GCP_PROJECTS_WITH_ORG_PARENT,
)
def test_sync_gcp_projects_with_org_parent(
    _mock_get_projects, _mock_get_orgs, neo4j_session
) -> None:
    """Test sync_gcp_projects handles projects with org as direct parent correctly."""
    neo4j_session.run("MATCH (n) DETACH DELETE n")

    # Sync org first
    cartography.intel.gcp.crm.orgs.sync_gcp_organizations(
        neo4j_session, TEST_UPDATE_TAG, COMMON_JOB_PARAMS
    )

    # Sync projects with org as direct parent
    cartography.intel.gcp.crm.projects.sync_gcp_projects(
        neo4j_session,
        "organizations/1337",
        [],  # No folders
        TEST_UPDATE_TAG,
        COMMON_JOB_PARAMS,
    )

    # Verify project nodes
    assert check_nodes(neo4j_session, "GCPProject", ["id"]) == {("project-abc",)}

    # Verify project -> org PARENT relationship
    assert check_rels(
        neo4j_session,
        "GCPProject",
        "id",
        "GCPOrganization",
        "id",
        "PARENT",
        rel_direction_right=True,
    ) == {("project-abc", "organizations/1337")}

    # Verify org -> project RESOURCE relationship
    assert check_rels(
        neo4j_session,
        "GCPOrganization",
        "id",
        "GCPProject",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {("organizations/1337", "project-abc")}

    # Verify no project -> folder PARENT relationship
    assert (
        check_rels(
            neo4j_session,
            "GCPProject",
            "id",
            "GCPFolder",
            "id",
            "PARENT",
            rel_direction_right=True,
        )
        == set()
    )
