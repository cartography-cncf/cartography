import cartography.intel.digitalocean.compute
import tests.data.digitalocean.compute

TEST_UPDATE_TAG = 123456789


def test_transform_and_load_droplets(neo4j_session):
    droplet_res = tests.data.digitalocean.compute.DROPLETS_RESPONSE
    test_droplet = droplet_res[0]
    account_id = 1
    project_id = "project_1"
    project_resources = {
        str(project_id): [
            "do:droplet:" + test_droplet.id,
        ],
    }

    """
    Test that we can correctly transform and load DODroplet nodes to Neo4j.
    """
    droplet_list = cartography.intel.digitalocean.compute.transform_droplets(
        droplet_res,
        account_id,
        project_resources,
    )
    cartography.intel.digitalocean.compute.load_droplets(
        neo4j_session,
        droplet_list,
        TEST_UPDATE_TAG,
    )

    query = """
        MATCH(d:DODroplet{id:$DropletId})
        RETURN d.id, d.name, d.ip_address, d.image, d.region, d.project_id, d.account_id, d.lastupdated
        """
    nodes = neo4j_session.run(
        query,
        DropletId=test_droplet.id,
    )
    actual_nodes = {
        (
            n["d.id"],
            n["d.name"],
            n["d.ip_address"],
            n["d.image"],
            n["d.region"],
            n["d.project_id"],
            n["d.account_id"],
            n["d.lastupdated"],
        )
        for n in nodes
    }
    expected_nodes = {
        (
            test_droplet.id,
            test_droplet.name,
            test_droplet.ip_address,
            test_droplet.image["slug"],
            test_droplet.region["slug"],
            project_id,
            account_id,
            TEST_UPDATE_TAG,
        ),
    }
    assert actual_nodes == expected_nodes
