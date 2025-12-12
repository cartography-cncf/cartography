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
    cartography.intel.gcp.crm.folders,
    "get_gcp_folders",
    return_value=tests.data.gcp.crm.GCP_FOLDERS,
)
def test_sync_gcp_folders(mock_get_folders, neo4j_session):
    # Pre-load org first
    cartography.intel.gcp.crm.orgs.load_gcp_organizations(
        neo4j_session, tests.data.gcp.crm.GCP_ORGANIZATIONS, TEST_UPDATE_TAG
    )

    # Load folders
    cartography.intel.gcp.crm.folders.sync_gcp_folders(
        neo4j_session,
        gcp_update_tag=TEST_UPDATE_TAG,
        common_job_parameters=COMMON_JOB_PARAMS,
        org_resource_name="organizations/1337",
    )

    # Load projects after folders exist
    cartography.intel.gcp.crm.projects.load_gcp_projects(
        neo4j_session,
        tests.data.gcp.crm.GCP_PROJECTS,
        TEST_UPDATE_TAG,
        org_resource_name="organizations/1337",
    )

    assert check_nodes(neo4j_session, "GCPFolder", ["id", "displayname"]) == {
        ("folders/1414", "my-folder"),
    }

    assert check_rels(
        neo4j_session,
        "GCPFolder",
        "id",
        "GCPOrganization",
        "id",
        "PARENT",
    ) == {("folders/1414", "organizations/1337")}

    assert check_rels(
        neo4j_session,
        "GCPOrganization",
        "id",
        "GCPFolder",
        "id",
        "RESOURCE",
    ) == {("organizations/1337", "folders/1414")}

    assert check_rels(
        neo4j_session,
        "GCPProject",
        "id",
        "GCPFolder",
        "id",
        "PARENT",
    ) == {("this-project-has-a-parent-232323", "folders/1414")}


@patch.object(
    cartography.intel.gcp.crm.folders,
    "get_gcp_folders",
    return_value=tests.data.gcp.crm.GCP_NESTED_FOLDERS,
)
def test_sync_gcp_nested_folders(_mock_get_folders, neo4j_session) -> None:
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    cartography.intel.gcp.crm.orgs.load_gcp_organizations(
        neo4j_session, tests.data.gcp.crm.GCP_ORGANIZATIONS, TEST_UPDATE_TAG
    )

    cartography.intel.gcp.crm.folders.sync_gcp_folders(
        neo4j_session,
        gcp_update_tag=TEST_UPDATE_TAG,
        common_job_parameters=COMMON_JOB_PARAMS,
        org_resource_name="organizations/1337",
    )

    assert check_nodes(neo4j_session, "GCPFolder", ["id", "displayname"]) == {
        ("folders/2000", "parent-folder"),
        ("folders/2001", "child-folder"),
    }

    assert check_rels(
        neo4j_session,
        "GCPFolder",
        "id",
        "GCPOrganization",
        "id",
        "PARENT",
    ) == {("folders/2000", "organizations/1337")}

    assert check_rels(
        neo4j_session,
        "GCPOrganization",
        "id",
        "GCPFolder",
        "id",
        "RESOURCE",
    ) == {
        ("organizations/1337", "folders/2000"),
        ("organizations/1337", "folders/2001"),
    }

    assert check_rels(
        neo4j_session,
        "GCPFolder",
        "id",
        "GCPFolder",
        "id",
        "PARENT",
    ) == {("folders/2001", "folders/2000")}
