from unittest.mock import patch

import cartography.intel.gcp.crm
import tests.data.gcp.crm
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
COMMON_JOB_PARAMS = {"UPDATE_TAG": TEST_UPDATE_TAG}


@patch.object(
    cartography.intel.gcp.crm,
    "get_gcp_folders",
    return_value=tests.data.gcp.crm.GCP_FOLDERS,
)
def test_sync_gcp_folders(mock_get_folders, neo4j_session):
    """Test that sync_gcp_folders creates GCPFolder nodes and relationships."""
    # Arrange
    # Pre-load the organization so that the folder has a parent to connect to
    cartography.intel.gcp.crm.load_gcp_organizations(
        neo4j_session,
        tests.data.gcp.crm.GCP_ORGANIZATIONS,
        TEST_UPDATE_TAG,
    )
    # Pre-load a project so that the folder has a child relationship
    cartography.intel.gcp.crm.load_gcp_projects(
        neo4j_session,
        tests.data.gcp.crm.GCP_PROJECTS,
        TEST_UPDATE_TAG,
    )

    # Act
    cartography.intel.gcp.crm.sync_gcp_folders(
        neo4j_session,
        crm_v2=None,
        gcp_update_tag=TEST_UPDATE_TAG,
        common_job_parameters={"UPDATE_TAG": TEST_UPDATE_TAG},
    )

    # Assert
    expected_nodes = {
        ("folders/1414", "my-folder"),
    }
    assert (
        check_nodes(neo4j_session, "GCPFolder", ["id", "displayname"]) == expected_nodes
    )

    expected_rels_org = {
        ("organizations/1337", "folders/1414"),
    }
    assert (
        check_rels(
            neo4j_session,
            "GCPOrganization",
            "id",
            "GCPFolder",
            "id",
            "RESOURCE",
        )
        == expected_rels_org
    )

    expected_rels_project = {
        ("folders/1414", "this-project-has-a-parent-232323"),
    }
    assert (
        check_rels(
            neo4j_session,
            "GCPFolder",
            "id",
            "GCPProject",
            "id",
            "RESOURCE",
        )
        == expected_rels_project
    )


def test_load_gcp_projects(neo4j_session):
    """
    Tests that we correctly load a sample hierarchy chain of GCP organizations to folders to projects.
    """
    # Clear database to ensure test isolation
    neo4j_session.run("MATCH (n) DETACH DELETE n")

    cartography.intel.gcp.crm.load_gcp_organizations(
        neo4j_session,
        tests.data.gcp.crm.GCP_ORGANIZATIONS,
        TEST_UPDATE_TAG,
    )
    cartography.intel.gcp.crm.load_gcp_folders(
        neo4j_session,
        tests.data.gcp.crm.GCP_FOLDERS,
        TEST_UPDATE_TAG,
    )
    cartography.intel.gcp.crm.load_gcp_projects(
        neo4j_session,
        tests.data.gcp.crm.GCP_PROJECTS,
        TEST_UPDATE_TAG,
    )

    # Ensure the sample project gets ingested correctly
    expected_nodes = {
        ("this-project-has-a-parent-232323"),
    }
    nodes = neo4j_session.run(
        """
        MATCH (d:GCPProject) return d.id
        """,
    )
    actual_nodes = {(n["d.id"]) for n in nodes}
    assert actual_nodes == expected_nodes

    # Expect (GCPProject{project-232323})<-[:RESOURCE]-(GCPFolder{1414})
    #             <-[:RESOURCE]-(GCPOrganization{1337}) to be connected
    query = """
    MATCH (p:GCPProject{id:$ProjectId})<-[:RESOURCE]-(f:GCPFolder)<-[:RESOURCE]-(o:GCPOrganization)
    RETURN p.id, f.id, o.id
    """
    nodes = neo4j_session.run(
        query,
        ProjectId="this-project-has-a-parent-232323",
    )
    actual_nodes = {
        (
            n["p.id"],
            n["f.id"],
            n["o.id"],
        )
        for n in nodes
    }
    expected_nodes = {
        (
            "this-project-has-a-parent-232323",
            "folders/1414",
            "organizations/1337",
        ),
    }
    assert actual_nodes == expected_nodes


def test_load_gcp_projects_without_parent(neo4j_session):
    """
    Ensure that the sample GCPProject that doesn't have a parent node gets ingested correctly.
    """
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")

    # Act
    cartography.intel.gcp.crm.load_gcp_projects(
        neo4j_session,
        tests.data.gcp.crm.GCP_PROJECTS_WITHOUT_PARENT,
        TEST_UPDATE_TAG,
    )

    # Assert
    expected_nodes = {
        ("my-parentless-project-987654"),
    }
    nodes = neo4j_session.run(
        """
        MATCH (d:GCPProject) WHERE NOT (d)<-[:RESOURCE]-() RETURN d.id
        """,
    )
    actual_nodes = {(n["d.id"]) for n in nodes}
    assert actual_nodes == expected_nodes


@patch.object(
    cartography.intel.gcp.crm,
    "get_gcp_organizations",
    return_value=tests.data.gcp.crm.GCP_ORGANIZATIONS,
)
@patch.object(
    cartography.intel.gcp.crm,
    "get_gcp_folders",
    return_value=tests.data.gcp.crm.GCP_FOLDERS,
)
def test_sync_gcp_projects(
    _mock_get_folders,
    _mock_get_orgs,
    neo4j_session,
) -> None:
    """Test that sync_gcp_projects ingests project data and connects hierarchy."""
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    cartography.intel.gcp.crm.sync_gcp_organizations(
        neo4j_session,
        None,
        TEST_UPDATE_TAG,
        COMMON_JOB_PARAMS,
    )
    cartography.intel.gcp.crm.sync_gcp_folders(
        neo4j_session,
        None,
        TEST_UPDATE_TAG,
        COMMON_JOB_PARAMS,
    )

    # Act
    cartography.intel.gcp.crm.sync_gcp_projects(
        neo4j_session,
        tests.data.gcp.crm.GCP_PROJECTS,
        TEST_UPDATE_TAG,
        COMMON_JOB_PARAMS,
    )

    # Assert
    assert check_nodes(neo4j_session, "GCPProject", ["id"]) == {
        ("this-project-has-a-parent-232323",),
    }

    query = """
        MATCH (p:GCPProject{id:$ProjectId})<-[:RESOURCE]-(f:GCPFolder)<-[:RESOURCE]-(o:GCPOrganization)
        RETURN p.id, f.id, o.id
    """
    nodes = neo4j_session.run(
        query,
        ProjectId="this-project-has-a-parent-232323",
    )
    actual_nodes = {
        (
            n["p.id"],
            n["f.id"],
            n["o.id"],
        )
        for n in nodes
    }
    assert actual_nodes == {
        (
            "this-project-has-a-parent-232323",
            "folders/1414",
            "organizations/1337",
        ),
    }


def test_sync_gcp_projects_without_parent(neo4j_session) -> None:
    """Ensure sync_gcp_projects handles projects with no parent."""
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")

    # Act
    cartography.intel.gcp.crm.sync_gcp_projects(
        neo4j_session,
        tests.data.gcp.crm.GCP_PROJECTS_WITHOUT_PARENT,
        TEST_UPDATE_TAG,
        COMMON_JOB_PARAMS,
    )

    # Assert
    assert check_nodes(neo4j_session, "GCPProject", ["id"]) == {
        ("my-parentless-project-987654",),
    }
    assert (
        check_rels(
            neo4j_session,
            "GCPFolder",
            "id",
            "GCPProject",
            "id",
            "RESOURCE",
        )
        == set()
    )


@patch.object(
    cartography.intel.gcp.crm,
    "get_gcp_organizations",
    return_value=tests.data.gcp.crm.GCP_ORGANIZATIONS,
)
@patch.object(
    cartography.intel.gcp.crm,
    "get_gcp_folders",
    return_value=tests.data.gcp.crm.GCP_FOLDERS,
)
def test_sync_gcp_projects_cleanup(
    _mock_get_folders,
    _mock_get_orgs,
    neo4j_session,
) -> None:
    """Ensure sync_gcp_projects cleanup removes stale project nodes."""
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    cartography.intel.gcp.crm.load_gcp_projects(
        neo4j_session,
        tests.data.gcp.crm.GCP_PROJECTS_WITHOUT_PARENT,
        TEST_UPDATE_TAG - 1,
    )

    cartography.intel.gcp.crm.sync_gcp_organizations(
        neo4j_session,
        None,
        TEST_UPDATE_TAG,
        COMMON_JOB_PARAMS,
    )
    cartography.intel.gcp.crm.sync_gcp_folders(
        neo4j_session,
        None,
        TEST_UPDATE_TAG,
        COMMON_JOB_PARAMS,
    )

    # Act
    cartography.intel.gcp.crm.sync_gcp_projects(
        neo4j_session,
        tests.data.gcp.crm.GCP_PROJECTS,
        TEST_UPDATE_TAG,
        COMMON_JOB_PARAMS,
    )

    # Assert
    assert check_nodes(neo4j_session, "GCPProject", ["id"]) == {
        ("this-project-has-a-parent-232323",),
    }


@patch.object(
    cartography.intel.gcp.crm,
    "get_gcp_folders",
    return_value=tests.data.gcp.crm.GCP_NESTED_FOLDERS,
)
def test_sync_gcp_nested_folders(_mock_get_folders, neo4j_session) -> None:
    """Ensure folder within folder relationships are created."""
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    cartography.intel.gcp.crm.load_gcp_organizations(
        neo4j_session,
        tests.data.gcp.crm.GCP_ORGANIZATIONS,
        TEST_UPDATE_TAG,
    )

    # Act
    cartography.intel.gcp.crm.sync_gcp_folders(
        neo4j_session,
        crm_v2=None,
        gcp_update_tag=TEST_UPDATE_TAG,
        common_job_parameters={"UPDATE_TAG": TEST_UPDATE_TAG},
    )

    # Assert nodes
    expected_nodes = {
        ("folders/2000", "parent-folder"),
        ("folders/2001", "child-folder"),
    }
    assert (
        check_nodes(neo4j_session, "GCPFolder", ["id", "displayname"]) == expected_nodes
    )

    # Assert org -> parent folder
    assert check_rels(
        neo4j_session,
        "GCPOrganization",
        "id",
        "GCPFolder",
        "id",
        "RESOURCE",
    ) == {("organizations/1337", "folders/2000")}

    # Assert parent folder -> child folder
    assert check_rels(
        neo4j_session,
        "GCPFolder",
        "id",
        "GCPFolder",
        "id",
        "RESOURCE",
    ) == {("folders/2000", "folders/2001")}


def test_sync_gcp_projects_with_org_parent(neo4j_session) -> None:
    """Ensure a project with organization parent links directly to the organization."""
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    cartography.intel.gcp.crm.load_gcp_organizations(
        neo4j_session,
        tests.data.gcp.crm.GCP_ORGANIZATIONS,
        TEST_UPDATE_TAG,
    )

    # Act
    cartography.intel.gcp.crm.sync_gcp_projects(
        neo4j_session,
        tests.data.gcp.crm.GCP_PROJECTS_WITH_ORG_PARENT,
        TEST_UPDATE_TAG,
        COMMON_JOB_PARAMS,
    )

    # Assert project node exists
    assert check_nodes(neo4j_session, "GCPProject", ["id"]) == {
        ("project-under-org-55555",),
    }

    # Assert organization -> project relationship
    assert check_rels(
        neo4j_session,
        "GCPOrganization",
        "id",
        "GCPProject",
        "id",
        "RESOURCE",
    ) == {("organizations/1337", "project-under-org-55555")}

    # Assert there is no folder -> project relationship for this project
    assert (
        check_rels(
            neo4j_session,
            "GCPFolder",
            "id",
            "GCPProject",
            "id",
            "RESOURCE",
        )
        == set()
    )
