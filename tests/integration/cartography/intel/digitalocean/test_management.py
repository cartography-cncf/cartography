import cartography.intel.digitalocean.management
import tests.data.digitalocean.management

TEST_UPDATE_TAG = 123456789


def test_transform_and_load_projects(neo4j_session):
    projects_res = tests.data.digitalocean.management.PROJECTS_RESPONSE
    test_project = projects_res[0]
    account_id = 1

    """
    Test that we can correctly transform and load DOProject nodes to Neo4j.
    """
    projects_list = cartography.intel.digitalocean.management.transform_projects(
        projects_res,
        account_id,
    )
    cartography.intel.digitalocean.management.load_projects(
        neo4j_session,
        projects_list,
        TEST_UPDATE_TAG,
    )

    query = """
        MATCH(p:DOProject{id:$ProjectId})
        RETURN p.id, p.name, p.owner_uuid, p.description, p.is_default, p.created_at, p.updated_at, p.account_id,
        p.lastupdated
        """
    nodes = neo4j_session.run(
        query,
        ProjectId=test_project.id,
    )
    actual_nodes = {
        (
            n["p.id"],
            n["p.name"],
            n["p.owner_uuid"],
            n["p.description"],
            n["p.is_default"],
            n["p.created_at"],
            n["p.updated_at"],
            n["p.account_id"],
            n["p.lastupdated"],
        )
        for n in nodes
    }
    expected_nodes = {
        (
            test_project.id,
            test_project.name,
            test_project.owner_uuid,
            test_project.description,
            test_project.is_default,
            test_project.created_at,
            test_project.updated_at,
            account_id,
            TEST_UPDATE_TAG,
        ),
    }
    assert actual_nodes == expected_nodes
