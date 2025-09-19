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


def test_load_gcp_projects(neo4j_session):
    neo4j_session.run("MATCH (n) DETACH DELETE n")

    cartography.intel.gcp.crm.orgs.load_gcp_organizations(
        neo4j_session, tests.data.gcp.crm.GCP_ORGANIZATIONS, TEST_UPDATE_TAG
    )
    cartography.intel.gcp.crm.folders.load_gcp_folders(
        neo4j_session,
        tests.data.gcp.crm.GCP_FOLDERS,
        TEST_UPDATE_TAG,
        org_resource_name="organizations/1337",
    )
    cartography.intel.gcp.crm.projects.load_gcp_projects(
        neo4j_session,
        tests.data.gcp.crm.GCP_PROJECTS,
        TEST_UPDATE_TAG,
        org_resource_name="organizations/1337",
    )

    nodes = neo4j_session.run("MATCH (d:GCPProject) return d.id")
    assert {(n["d.id"]) for n in nodes} == {"this-project-has-a-parent-232323"}

    query = (
        "MATCH (p:GCPProject{id:$ProjectId})-[:PARENT]->(f:GCPFolder)-[:PARENT]->(o:GCPOrganization)\n"
        "RETURN p.id, f.id, o.id"
    )
    nodes = neo4j_session.run(query, ProjectId="this-project-has-a-parent-232323")
    assert {(n["p.id"], n["f.id"], n["o.id"]) for n in nodes} == {
        ("this-project-has-a-parent-232323", "folders/1414", "organizations/1337")
    }


def test_load_gcp_projects_without_parent(neo4j_session):
    neo4j_session.run("MATCH (n) DETACH DELETE n")

    cartography.intel.gcp.crm.orgs.load_gcp_organizations(
        neo4j_session, tests.data.gcp.crm.GCP_ORGANIZATIONS, TEST_UPDATE_TAG
    )
    cartography.intel.gcp.crm.projects.load_gcp_projects(
        neo4j_session,
        tests.data.gcp.crm.GCP_PROJECTS_WITHOUT_PARENT,
        TEST_UPDATE_TAG,
        org_resource_name="organizations/1337",
    )

    nodes = neo4j_session.run(
        "MATCH (d:GCPProject) WHERE NOT (d)-[:PARENT]->(:GCPFolder) RETURN d.id"
    )
    assert {(n["d.id"]) for n in nodes} == {"my-parentless-project-987654"}


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
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    cartography.intel.gcp.crm.orgs.sync_gcp_organizations(
        neo4j_session, TEST_UPDATE_TAG, COMMON_JOB_PARAMS
    )
    folders = cartography.intel.gcp.crm.folders.sync_gcp_folders(
        neo4j_session,
        TEST_UPDATE_TAG,
        COMMON_JOB_PARAMS,
        org_resource_name="organizations/1337",
    )

    cartography.intel.gcp.crm.projects.sync_gcp_projects(
        neo4j_session,
        "organizations/1337",
        folders,
        TEST_UPDATE_TAG,
        COMMON_JOB_PARAMS,
    )

    assert check_nodes(neo4j_session, "GCPProject", ["id"]) == {
        ("this-project-has-a-parent-232323",)
    }

    query = (
        "MATCH (p:GCPProject{id:$ProjectId})-[:PARENT]->(f:GCPFolder)-[:PARENT]->(o:GCPOrganization)\n"
        "RETURN p.id, f.id, o.id"
    )
    nodes = neo4j_session.run(query, ProjectId="this-project-has-a-parent-232323")
    assert {(n["p.id"], n["f.id"], n["o.id"]) for n in nodes} == {
        ("this-project-has-a-parent-232323", "folders/1414", "organizations/1337")
    }


@patch.object(
    cartography.intel.gcp.crm.projects,
    "get_gcp_projects",
    return_value=tests.data.gcp.crm.GCP_PROJECTS_WITHOUT_PARENT,
)
def test_sync_gcp_projects_without_parent(_mock_get_projects, neo4j_session) -> None:
    neo4j_session.run("MATCH (n) DETACH DELETE n")

    cartography.intel.gcp.crm.orgs.load_gcp_organizations(
        neo4j_session, tests.data.gcp.crm.GCP_ORGANIZATIONS, TEST_UPDATE_TAG
    )
    cartography.intel.gcp.crm.projects.sync_gcp_projects(
        neo4j_session,
        "organizations/1337",
        [],  # No folders
        TEST_UPDATE_TAG,
        COMMON_JOB_PARAMS,
    )

    assert check_nodes(neo4j_session, "GCPProject", ["id"]) == {
        ("my-parentless-project-987654",)
    }
    assert (
        check_rels(neo4j_session, "GCPProject", "id", "GCPFolder", "id", "PARENT")
        == set()
    )


@patch.object(
    cartography.intel.gcp.crm.projects,
    "get_gcp_projects",
    return_value=tests.data.gcp.crm.GCP_PROJECTS_WITH_ORG_PARENT,
)
def test_sync_gcp_projects_with_org_parent(_mock_get_projects, neo4j_session) -> None:
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    cartography.intel.gcp.crm.orgs.load_gcp_organizations(
        neo4j_session, tests.data.gcp.crm.GCP_ORGANIZATIONS, TEST_UPDATE_TAG
    )

    cartography.intel.gcp.crm.projects.sync_gcp_projects(
        neo4j_session,
        "organizations/1337",
        [],  # No folders
        TEST_UPDATE_TAG,
        COMMON_JOB_PARAMS,
    )

    assert check_nodes(neo4j_session, "GCPProject", ["id"]) == {
        ("project-under-org-55555",)
    }
    assert check_rels(
        neo4j_session, "GCPProject", "id", "GCPOrganization", "id", "PARENT"
    ) == {("project-under-org-55555", "organizations/1337")}
    assert check_rels(
        neo4j_session, "GCPOrganization", "id", "GCPProject", "id", "RESOURCE"
    ) == {("organizations/1337", "project-under-org-55555")}
    assert (
        check_rels(neo4j_session, "GCPProject", "id", "GCPFolder", "id", "PARENT")
        == set()
    )
