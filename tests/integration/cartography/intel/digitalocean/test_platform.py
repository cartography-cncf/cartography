import cartography.intel.digitalocean.platform
import tests.data.digitalocean.platform

TEST_UPDATE_TAG = 123456789


def test_transform_and_load_account(neo4j_session):
    account_res = tests.data.digitalocean.platform.ACCOUNT_RESPONSE

    """
    Test that we can correctly transform and load DOAccount nodes to Neo4j.
    """
    account = cartography.intel.digitalocean.platform.transform_account(account_res)
    cartography.intel.digitalocean.platform.load_account(
        neo4j_session,
        account,
        TEST_UPDATE_TAG,
    )

    query = """
        MATCH(a:DOAccount{id:$AccountId})
        RETURN a.id, a.uuid, a.droplet_limit, a.floating_ip_limit, a.status, a.lastupdated
        """
    nodes = neo4j_session.run(
        query,
        AccountId=account_res.uuid,
    )
    actual_nodes = {
        (
            n["a.id"],
            n["a.uuid"],
            n["a.droplet_limit"],
            n["a.floating_ip_limit"],
            n["a.status"],
            n["a.lastupdated"],
        )
        for n in nodes
    }
    expected_nodes = {
        (
            account_res.uuid,
            account_res.uuid,
            account_res.droplet_limit,
            account_res.floating_ip_limit,
            account_res.status,
            TEST_UPDATE_TAG,
        ),
    }
    assert actual_nodes == expected_nodes
