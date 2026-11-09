import cartography.intel.ontology.publicips
from tests.integration.util import check_rels

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

        MERGE (eip:AWSElasticIPAddress {id: 'eip-1'})
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
        MATCH (:PublicIP {id: '203.0.113.10'})-[r:RESERVED_BY]->(:AWSElasticIPAddress {id: 'eip-1'})
        RETURN count(r) AS count
        """
    ).single()["count"]
    assert fresh_reserved_by_count == 1


def test_sync_links_dns_address_records_to_public_ips(neo4j_session):
    """A and AAAA records link to the PublicIP built from the provider IP they resolve to."""
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    neo4j_session.run(
        """
        CREATE (:AzurePublicIPAddress {id: 'pip-a', ip_address: '203.0.113.10'})
        CREATE (:AzurePublicIPAddress {id: 'pip-b', ip_address: '203.0.113.11'})
        CREATE (:AWSElasticIPAddress {id: 'eip', public_ip: '203.0.113.12'})
        CREATE (:AzurePublicIPAddress {id: 'pip-v6', ip_address: '2001:db8::1'})
        CREATE (:DNSRecord:AWSDNSRecord {
            id: 'route53-multi-value-a', _ont_type: 'A', _ont_value: '203.0.113.10,203.0.113.11'
        })
        CREATE (:DNSRecord:AWSDNSRecord {
            id: 'route53-aaaa', _ont_type: 'AAAA', _ont_value: '2001:DB8::1'
        })
        CREATE (:DNSRecord:GCPRecordSet {
            id: 'gcp-a', _ont_type: 'A', data: ['203.0.113.12']
        })
        CREATE (:DNSRecord {id: 'txt', _ont_type: 'TXT', _ont_value: '203.0.113.10'})
        """
    )

    # Act
    cartography.intel.ontology.publicips.sync(
        neo4j_session,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )

    # Assert
    assert check_rels(
        neo4j_session,
        "DNSRecord",
        "id",
        "PublicIP",
        "id",
        "DNS_POINTS_TO",
    ) == {
        ("route53-multi-value-a", "203.0.113.10"),
        ("route53-multi-value-a", "203.0.113.11"),
        ("route53-aaaa", "2001:db8::1"),
        ("gcp-a", "203.0.113.12"),
    }


def test_sync_removes_dns_link_when_record_moves_to_another_ip(neo4j_session):
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    neo4j_session.run(
        """
        CREATE (:AzurePublicIPAddress {id: 'old', ip_address: '203.0.113.10'})
        CREATE (:AzurePublicIPAddress {id: 'new', ip_address: '203.0.113.20'})
        CREATE (:DNSRecord {id: 'app', _ont_type: 'A', _ont_value: '203.0.113.10'})
        """
    )
    cartography.intel.ontology.publicips.sync(
        neo4j_session,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )
    neo4j_session.run(
        "MATCH (d:DNSRecord {id: 'app'}) SET d._ont_value = '203.0.113.20'"
    )

    # Act
    cartography.intel.ontology.publicips.sync(
        neo4j_session,
        TEST_UPDATE_TAG + 1,
        {"UPDATE_TAG": TEST_UPDATE_TAG + 1},
    )

    # Assert
    assert check_rels(
        neo4j_session,
        "DNSRecord",
        "id",
        "PublicIP",
        "id",
        "DNS_POINTS_TO",
    ) == {("app", "203.0.113.20")}
