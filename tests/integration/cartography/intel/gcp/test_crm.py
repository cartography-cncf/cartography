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


def test_sync_gcp_organizations(neo4j_session):
    """
    Test that sync_gcp_organizations correctly syncs GCP organizations to Neo4j.
    """
    common_job_parameters = {"UPDATE_TAG": TEST_UPDATE_TAG}

    # Load organizations
    cartography.intel.gcp.crm.load_gcp_organizations(
        neo4j_session,
        tests.data.gcp.crm.GCP_ORGANIZATIONS,
        TEST_UPDATE_TAG,
    )

    # Verify organizations are loaded correctly
    expected_nodes = {"organizations/1337"}
    nodes = neo4j_session.run("MATCH (o:GCPOrganization) RETURN o.id")
    actual_nodes = {n["o.id"] for n in nodes}
    assert actual_nodes == expected_nodes

    #  Verify organization properties
    org_query = """
    MATCH (o:GCPOrganization{id: 'organizations/1337'}) 
    RETURN o.displayname, o.lifecyclestate, o.lastupdated
    """
    result = neo4j_session.run(org_query).single()
    assert result["o.displayname"] == "example.com"
    assert result["o.lifecyclestate"] == "ACTIVE"
    assert result["o.lastupdated"] == TEST_UPDATE_TAG


def test_sync_gcp_folders(neo4j_session):
    """
    Test that sync_gcp_folders correctly syncs GCP folders to Neo4j.
    """
    # Load parent organization
    cartography.intel.gcp.crm.load_gcp_organizations(
        neo4j_session,
        tests.data.gcp.crm.GCP_ORGANIZATIONS,
        TEST_UPDATE_TAG,
    )

    common_job_parameters = {"UPDATE_TAG": TEST_UPDATE_TAG}

    # Load folders
    cartography.intel.gcp.crm.load_gcp_folders(
        neo4j_session,
        tests.data.gcp.crm.GCP_FOLDERS,
        TEST_UPDATE_TAG,
    )

    # Verify folders are loaded correctly
    expected_nodes = {"folders/1414"}
    nodes = neo4j_session.run("MATCH (f:GCPFolder) RETURN f.id")
    actual_nodes = {n["f.id"] for n in nodes}
    assert actual_nodes == expected_nodes

    # Verify folder properties
    folder_query = """
    MATCH (f:GCPFolder{id: 'folders/1414'}) 
    RETURN f.displayname, f.lifecyclestate, f.lastupdated
    """
    result = neo4j_session.run(folder_query).single()
    assert result["f.displayname"] == "my-folder"
    assert result["f.lifecyclestate"] == "ACTIVE"
    assert result["f.lastupdated"] == TEST_UPDATE_TAG

    # Verify relationship: Organization -> Folder
    relationship_query = """
    MATCH (o:GCPOrganization{id: 'organizations/1337'})-[:RESOURCE]->(f:GCPFolder{id: 'folders/1414'})
    RETURN COUNT(*) as count
    """
    result = neo4j_session.run(relationship_query).single()
    assert result["count"] == 1


def test_sync_gcp_projects(neo4j_session):
    """
    Test that sync_gcp_projects correctly syncs GCP projects to Neo4j.
    """
    # Clear existing project nodes
    neo4j_session.run("MATCH (p:GCPProject) DETACH DELETE p")

    # Load referenced parent organization and folder
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

    common_job_parameters = {"UPDATE_TAG": TEST_UPDATE_TAG}

    # Run sync
    cartography.intel.gcp.crm.sync_gcp_projects(
        neo4j_session,
        tests.data.gcp.crm.GCP_PROJECTS,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    expected_nodes = {"this-project-has-a-parent-232323"}
    nodes = neo4j_session.run("MATCH (p:GCPProject) RETURN p.id")
    actual_nodes = {n["p.id"] for n in nodes}
    assert actual_nodes == expected_nodes

    # project properties
    project_query = """
    MATCH (p:GCPProject{id: 'this-project-has-a-parent-232323'}) 
    RETURN p.projectnumber, p.displayname, p.lifecyclestate, p.lastupdated
    """
    result = neo4j_session.run(project_query).single()
    assert result["p.projectnumber"] == "232323"
    assert result["p.displayname"] == "Group 1"
    assert result["p.lifecyclestate"] == "ACTIVE"
    assert result["p.lastupdated"] == TEST_UPDATE_TAG

    #  Organization -> Folder -> Project
    hierarchy_query = """
    MATCH (o:GCPOrganization{id: 'organizations/1337'})-[:RESOURCE]->(f:GCPFolder{id: 'folders/1414'})-[:RESOURCE]->(p:GCPProject{id: 'this-project-has-a-parent-232323'})
    RETURN COUNT(*) as count
    """
    result = neo4j_session.run(hierarchy_query).single()
    assert result["count"] == 1
