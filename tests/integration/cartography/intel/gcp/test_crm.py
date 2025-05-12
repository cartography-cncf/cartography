import cartography.intel.gcp.crm
import tests.data.gcp.crm

TEST_UPDATE_TAG = 123456789


def test_load_gcp_projects(neo4j_session):
    """
    Tests that we correctly load a sample hierarchy chain of GCP organizations to folders to projects.
    """
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
    cartography.intel.gcp.crm.load_gcp_projects(
        neo4j_session,
        tests.data.gcp.crm.GCP_PROJECTS_WITHOUT_PARENT,
        TEST_UPDATE_TAG,
    )

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
