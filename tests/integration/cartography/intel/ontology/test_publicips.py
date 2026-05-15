import cartography.intel.ontology.publicips

TEST_UPDATE_TAG = 123456789


def test_cleanup_removes_stale_publicip_points_to_device_relationships(neo4j_session):
    """PublicIP cleanup should delete stale custom ontology-derived POINTS_TO Device edges."""
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    stale_tag = TEST_UPDATE_TAG - 1

    neo4j_session.run(
        """
        MERGE (ip:PublicIP:Ontology {id: '203.0.113.10'})
        SET ip.ip_address = '203.0.113.10',
            ip.lastupdated = $update_tag

        MERGE (device:Device:Ontology {id: 'device-1'})
        SET device.serial_number = 'device-1',
            device.lastupdated = $update_tag

        MERGE (eip:ElasticIPAddress {id: 'eip-1'})
        SET eip.public_ip = '203.0.113.10'

        MERGE (ip)-[stale_points_to:POINTS_TO]->(device)
        SET stale_points_to.lastupdated = $stale_tag

        MERGE (ip)-[fresh_reserved_by:RESERVED_BY]->(eip)
        SET fresh_reserved_by.lastupdated = $update_tag
        """,
        update_tag=TEST_UPDATE_TAG,
        stale_tag=stale_tag,
    )

    cartography.intel.ontology.publicips.cleanup(
        neo4j_session,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )

    stale_points_to_count = neo4j_session.run(
        """
        MATCH (:PublicIP {id: '203.0.113.10'})-[r:POINTS_TO]->(:Device {id: 'device-1'})
        RETURN count(r) AS count
        """
    ).single()["count"]
    assert stale_points_to_count == 0

    fresh_reserved_by_count = neo4j_session.run(
        """
        MATCH (:PublicIP {id: '203.0.113.10'})-[r:RESERVED_BY]->(:ElasticIPAddress {id: 'eip-1'})
        RETURN count(r) AS count
        """
    ).single()["count"]
    assert fresh_reserved_by_count == 1
