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
def test_sync_gcp_folders(
    _mock_get_projects, _mock_get_folders, _mock_get_orgs, neo4j_session
):
    """Test sync_gcp_folders creates folder nodes and relationships to org and projects."""
    neo4j_session.run("MATCH (n) DETACH DELETE n")

    # Sync org first
    cartography.intel.gcp.crm.orgs.sync_gcp_organizations(
        neo4j_session, TEST_UPDATE_TAG, COMMON_JOB_PARAMS
    )

    # Sync folders
    folders = cartography.intel.gcp.crm.folders.sync_gcp_folders(
        neo4j_session,
        gcp_update_tag=TEST_UPDATE_TAG,
        common_job_parameters=COMMON_JOB_PARAMS,
        org_resource_name="organizations/1337",
    )

    # Sync projects after folders exist
    cartography.intel.gcp.crm.projects.sync_gcp_projects(
        neo4j_session,
        "organizations/1337",
        folders,
        TEST_UPDATE_TAG,
        COMMON_JOB_PARAMS,
    )

    # Verify folder nodes
    assert check_nodes(neo4j_session, "GCPFolder", ["id", "displayname"]) == {
        ("folders/1414", "my-folder"),
    }

    # Verify folder -> org PARENT relationship
    assert check_rels(
        neo4j_session,
        "GCPFolder",
        "id",
        "GCPOrganization",
        "id",
        "PARENT",
        rel_direction_right=True,
    ) == {("folders/1414", "organizations/1337")}

    # Verify org -> folder RESOURCE relationship
    assert check_rels(
        neo4j_session,
        "GCPOrganization",
        "id",
        "GCPFolder",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {("organizations/1337", "folders/1414")}

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


@patch.object(
    cartography.intel.gcp.crm.orgs,
    "get_gcp_organizations",
    return_value=tests.data.gcp.crm.GCP_ORGANIZATIONS,
)
@patch.object(
    cartography.intel.gcp.crm.folders,
    "get_gcp_folders",
    return_value=tests.data.gcp.crm.GCP_NESTED_FOLDERS,
)
def test_sync_gcp_nested_folders(
    _mock_get_folders, _mock_get_orgs, neo4j_session
) -> None:
    """Test sync_gcp_folders handles nested folder hierarchies correctly."""
    neo4j_session.run("MATCH (n) DETACH DELETE n")

    # Sync org first
    cartography.intel.gcp.crm.orgs.sync_gcp_organizations(
        neo4j_session, TEST_UPDATE_TAG, COMMON_JOB_PARAMS
    )

    # Sync folders
    cartography.intel.gcp.crm.folders.sync_gcp_folders(
        neo4j_session,
        gcp_update_tag=TEST_UPDATE_TAG,
        common_job_parameters=COMMON_JOB_PARAMS,
        org_resource_name="organizations/1337",
    )

    # Verify folder nodes
    assert check_nodes(neo4j_session, "GCPFolder", ["id", "displayname"]) == {
        ("folders/2000", "parent-folder"),
        ("folders/2001", "child-folder"),
    }

    # Verify parent folder -> org PARENT relationship
    assert check_rels(
        neo4j_session,
        "GCPFolder",
        "id",
        "GCPOrganization",
        "id",
        "PARENT",
        rel_direction_right=True,
    ) == {("folders/2000", "organizations/1337")}

    # Verify org -> all folders RESOURCE relationship
    assert check_rels(
        neo4j_session,
        "GCPOrganization",
        "id",
        "GCPFolder",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        ("organizations/1337", "folders/2000"),
        ("organizations/1337", "folders/2001"),
    }

    # Verify child folder -> parent folder PARENT relationship
    assert check_rels(
        neo4j_session,
        "GCPFolder",
        "id",
        "GCPFolder",
        "id",
        "PARENT",
        rel_direction_right=True,
    ) == {("folders/2001", "folders/2000")}
