import cartography.intel.gcp.dns
import tests.data.gcp.dns

TEST_PROJECT_NUMBER = "000000000000"
TEST_UPDATE_TAG = 123456789


def test_load_dns_zones(neo4j_session):
    data = tests.data.gcp.dns.DNS_ZONES
    cartography.intel.gcp.dns.load_dns_zones(
        neo4j_session,
        data,
        TEST_PROJECT_NUMBER,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        # flake8: noqa
        "111111111111111111111",
        "2222222222222222222",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:GCPDNSZone) RETURN r.id;
        """,
    )

    actual_nodes = {n["r.id"] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_rrs(neo4j_session):
    data = tests.data.gcp.dns.DNS_RRS
    cartography.intel.gcp.dns.load_rrs(
        neo4j_session,
        data,
        TEST_PROJECT_NUMBER,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        # flake8: noqa
        "a.zone-1.example.com.",
        "b.zone-1.example.com.",
        "a.zone-2.example.com.",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:GCPRecordSet) RETURN r.id;
        """,
    )

    actual_nodes = {n["r.id"] for n in nodes}

    assert actual_nodes == expected_nodes


def test_zones_relationships(neo4j_session):
    # Create Test GCPProject
    neo4j_session.run(
        """
        MERGE (gcp:GCPProject{id: $PROJECT_NUMBER})
        ON CREATE SET gcp.firstseen = timestamp()
        SET gcp.lastupdated = $UPDATE_TAG
        """,
        PROJECT_NUMBER=TEST_PROJECT_NUMBER,
        UPDATE_TAG=TEST_UPDATE_TAG,
    )

    # Load Test DNS Zone
    data = tests.data.gcp.dns.DNS_ZONES
    cartography.intel.gcp.dns.load_dns_zones(
        neo4j_session,
        data,
        TEST_PROJECT_NUMBER,
        TEST_UPDATE_TAG,
    )

    expected = {
        (TEST_PROJECT_NUMBER, "111111111111111111111"),
        (TEST_PROJECT_NUMBER, "2222222222222222222"),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:GCPProject)-[:RESOURCE]->(n2:GCPDNSZone) RETURN n1.id, n2.id;
        """,
    )

    actual = {(r["n1.id"], r["n2.id"]) for r in result}

    assert actual == expected


def test_rrs_relationships(neo4j_session):
    # Load Test DNS Zone
    data = tests.data.gcp.dns.DNS_ZONES
    cartography.intel.gcp.dns.load_dns_zones(
        neo4j_session,
        data,
        TEST_PROJECT_NUMBER,
        TEST_UPDATE_TAG,
    )

    # Load Test RRS
    data = tests.data.gcp.dns.DNS_RRS
    cartography.intel.gcp.dns.load_rrs(
        neo4j_session,
        data,
        TEST_PROJECT_NUMBER,
        TEST_UPDATE_TAG,
    )

    expected = {
        ("111111111111111111111", "a.zone-1.example.com."),
        ("111111111111111111111", "b.zone-1.example.com."),
        ("2222222222222222222", "a.zone-2.example.com."),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:GCPDNSZone)-[:HAS_RECORD]->(n2:GCPRecordSet) RETURN n1.id, n2.id;
        """,
    )

    actual = {(r["n1.id"], r["n2.id"]) for r in result}

    assert actual == expected

def test_sync(neo4j_session):
    """
    Test that DNS zones and record sets sync correctly into Neo4j.
    """
    
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
    }


    dns_zones_data = tests.data.gcp.dns.DNS_ZONES
    dns_rrs_data = tests.data.gcp.dns.DNS_RRS

    # Create test GCPProject
    neo4j_session.run(
        """
        MERGE (gcp:GCPProject {id: $PROJECT_NUMBER})
        ON CREATE SET gcp.firstseen = timestamp()
        SET gcp.lastupdated = $UPDATE_TAG
        """,
        PROJECT_NUMBER=TEST_PROJECT_NUMBER,
        UPDATE_TAG=TEST_UPDATE_TAG,
    )

    # Simulate sync's 
    cartography.intel.gcp.dns.load_dns_zones(
        neo4j_session,
        dns_zones_data,
        TEST_PROJECT_NUMBER,
        TEST_UPDATE_TAG,
    )
    cartography.intel.gcp.dns.load_rrs(
        neo4j_session,
        dns_rrs_data,
        TEST_PROJECT_NUMBER,
        TEST_UPDATE_TAG,
    )

    # Simulate cleanup
    cartography.intel.gcp.dns.cleanup_dns_records(
        neo4j_session,
        common_job_parameters,
    )

    # Verify DNS Zones
    expected_zone_nodes = {
        "111111111111111111111",
        "2222222222222222222",
    }
    zone_nodes = neo4j_session.run(
        "MATCH (r:GCPDNSZone) RETURN r.id",
    )
    actual_zone_nodes = {n["r.id"] for n in zone_nodes}
    assert actual_zone_nodes == expected_zone_nodes

    # Verify DNS Zone relationships to GCPProject
    expected_zone_relationships = {
        (TEST_PROJECT_NUMBER, "111111111111111111111"),
        (TEST_PROJECT_NUMBER, "2222222222222222222"),
    }
    zone_relationships = neo4j_session.run(
        """
        MATCH (n1:GCPProject)-[:RESOURCE]->(n2:GCPDNSZone)
        RETURN n1.id, n2.id
        """,
    )
    actual_zone_relationships = {
        (r["n1.id"], r["n2.id"]) for r in zone_relationships
    }
    assert actual_zone_relationships == expected_zone_relationships

    # Verify Resource Record Sets
    expected_rrs_nodes = {
        "a.zone-1.example.com.",
        "b.zone-1.example.com.",
        "a.zone-2.example.com.",
    }
    rrs_nodes = neo4j_session.run(
        "MATCH (r:GCPRecordSet) RETURN r.id",
    )
    actual_rrs_nodes = {n["r.id"] for n in rrs_nodes}
    assert actual_rrs_nodes == expected_rrs_nodes

    # Verify Resource Record Set relationships to DNS Zones
    expected_rrs_relationships = {
        ("111111111111111111111", "a.zone-1.example.com."),
        ("111111111111111111111", "b.zone-1.example.com."),
        ("2222222222222222222", "a.zone-2.example.com."),
    }
    rrs_relationships = neo4j_session.run(
        """
        MATCH (n1:GCPDNSZone)-[:HAS_RECORD]->(n2:GCPRecordSet)
        RETURN n1.id, n2.id
        """,
    )
    actual_rrs_relationships = {
        (r["n1.id"], r["n2.id"]) for r in rrs_relationships
    }
    assert actual_rrs_relationships == expected_rrs_relationships
