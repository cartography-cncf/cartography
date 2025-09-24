from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.gcp.dns
import tests.data.gcp.dns
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_PROJECT_ID = "000000000000"
TEST_PROJECT_NUMBER = "000000000000"
TEST_UPDATE_TAG = 123456789


def test_load_dns_zones(neo4j_session):
    data = cartography.intel.gcp.dns.transform_dns_zones(tests.data.gcp.dns.DNS_ZONES)
    cartography.intel.gcp.dns.load_dns_zones(
        neo4j_session,
        data,
        TEST_PROJECT_ID,
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
    # Ensure Test GCPProject exists to allow RESOURCE relationships to be created
    neo4j_session.run(
        """
        MERGE (p:GCPProject{id:$PROJECT_ID})
        ON CREATE SET p.firstseen = timestamp()
        SET p.lastupdated = $UPDATE_TAG
        """,
        PROJECT_ID=TEST_PROJECT_ID,
        UPDATE_TAG=TEST_UPDATE_TAG,
    )

    data = cartography.intel.gcp.dns.transform_dns_rrs(tests.data.gcp.dns.DNS_RRS)
    cartography.intel.gcp.dns.load_rrs(
        neo4j_session,
        data,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        # id is name|type|zone
        "a.zone-1.example.com.|TXT|111111111111111111111",
        "b.zone-1.example.com.|TXT|111111111111111111111",
        "a.zone-2.example.com.|TXT|2222222222222222222",
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
        MERGE (gcp:GCPProject{id: $PROJECT_ID})
        ON CREATE SET gcp.firstseen = timestamp()
        SET gcp.lastupdated = $UPDATE_TAG
        """,
        PROJECT_ID=TEST_PROJECT_ID,
        UPDATE_TAG=TEST_UPDATE_TAG,
    )

    # Load Test DNS Zone
    data = cartography.intel.gcp.dns.transform_dns_zones(tests.data.gcp.dns.DNS_ZONES)
    cartography.intel.gcp.dns.load_dns_zones(
        neo4j_session,
        data,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
    )

    expected = {
        (TEST_PROJECT_ID, "111111111111111111111"),
        (TEST_PROJECT_ID, "2222222222222222222"),
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
    # Ensure Test GCPProject exists to allow RESOURCE relationships to be created
    neo4j_session.run(
        """
        MERGE (p:GCPProject{id:$PROJECT_ID})
        ON CREATE SET p.firstseen = timestamp()
        SET p.lastupdated = $UPDATE_TAG
        """,
        PROJECT_ID=TEST_PROJECT_ID,
        UPDATE_TAG=TEST_UPDATE_TAG,
    )

    # Load Test DNS Zone
    data = cartography.intel.gcp.dns.transform_dns_zones(tests.data.gcp.dns.DNS_ZONES)
    cartography.intel.gcp.dns.load_dns_zones(
        neo4j_session,
        data,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
    )

    # Load Test RRS
    data = cartography.intel.gcp.dns.transform_dns_rrs(tests.data.gcp.dns.DNS_RRS)
    cartography.intel.gcp.dns.load_rrs(
        neo4j_session,
        data,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
    )

    expected_zone_rels = {
        ("111111111111111111111", "a.zone-1.example.com.|TXT|111111111111111111111"),
        ("111111111111111111111", "b.zone-1.example.com.|TXT|111111111111111111111"),
        ("2222222222222222222", "a.zone-2.example.com.|TXT|2222222222222222222"),
    }

    # Fetch zone -> record relationships
    result = neo4j_session.run(
        """
        MATCH (n1:GCPDNSZone)-[:HAS_RECORD]->(n2:GCPRecordSet) RETURN n1.id, n2.id;
        """,
    )
    actual_zone_rels = {(r["n1.id"], r["n2.id"]) for r in result}
    assert actual_zone_rels == expected_zone_rels

    # Project -> record relationships
    result = neo4j_session.run(
        """
        MATCH (p:GCPProject{id:$PROJECT})-[:RESOURCE]->(r:GCPRecordSet) RETURN p.id, r.id;
        """,
        PROJECT=TEST_PROJECT_NUMBER,
    )
    actual_proj_rels = {(r["p.id"], r["r.id"]) for r in result}
    expected_proj_rels = {
        (TEST_PROJECT_NUMBER, "a.zone-1.example.com.|TXT|111111111111111111111"),
        (TEST_PROJECT_NUMBER, "b.zone-1.example.com.|TXT|111111111111111111111"),
        (TEST_PROJECT_NUMBER, "a.zone-2.example.com.|TXT|2222222222222222222"),
    }
    assert actual_proj_rels == expected_proj_rels

    # Project -> record relationships
    result = neo4j_session.run(
        """
        MATCH (p:GCPProject{id:$PROJECT_ID})-[:RESOURCE]->(r:GCPRecordSet) RETURN p.id, r.id;
        """,
        PROJECT_ID=TEST_PROJECT_ID,
    )
    actual_proj_rels = {(r["p.id"], r["r.id"]) for r in result}
    expected_proj_rels = {
        (TEST_PROJECT_ID, "a.zone-1.example.com.|TXT|111111111111111111111"),
        (TEST_PROJECT_ID, "b.zone-1.example.com.|TXT|111111111111111111111"),
        (TEST_PROJECT_ID, "a.zone-2.example.com.|TXT|2222222222222222222"),
    }
    assert actual_proj_rels == expected_proj_rels


@patch.object(
    cartography.intel.gcp.dns,
    "get_dns_rrs",
    return_value=tests.data.gcp.dns.DNS_RRS,
)
@patch.object(
    cartography.intel.gcp.dns,
    "get_dns_zones",
    return_value=tests.data.gcp.dns.DNS_ZONES,
)
def test_sync_dns_records(mock_get_zones, mock_get_rrs, neo4j_session):
    """sync() loads DNS zones, record sets, and creates relationships."""
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "PROJECT_ID": TEST_PROJECT_ID,
    }

    # Ensure test GCPProject exists
    neo4j_session.run(
        """
        MERGE (p:GCPProject{id: $PROJECT_ID})
        ON CREATE SET p.firstseen = timestamp()
        SET p.lastupdated = $UPDATE_TAG
        """,
        PROJECT_ID=TEST_PROJECT_ID,
        UPDATE_TAG=TEST_UPDATE_TAG,
    )

    cartography.intel.gcp.dns.sync(
        neo4j_session,
        MagicMock(),
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    assert check_nodes(
        neo4j_session,
        "GCPDNSZone",
        ["id"],
    ) == {
        ("111111111111111111111",),
        ("2222222222222222222",),
    }
    assert check_nodes(
        neo4j_session,
        "GCPRecordSet",
        ["id"],
    ) == {
        ("a.zone-1.example.com.|TXT|111111111111111111111",),
        ("b.zone-1.example.com.|TXT|111111111111111111111",),
        ("a.zone-2.example.com.|TXT|2222222222222222222",),
    }
    assert check_rels(
        neo4j_session,
        "GCPProject",
        "id",
        "GCPDNSZone",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (TEST_PROJECT_ID, "111111111111111111111"),
        (TEST_PROJECT_ID, "2222222222222222222"),
    }
    assert check_rels(
        neo4j_session,
        "GCPDNSZone",
        "id",
        "GCPRecordSet",
        "id",
        "HAS_RECORD",
        rel_direction_right=True,
    ) == {
        ("111111111111111111111", "a.zone-1.example.com.|TXT|111111111111111111111"),
        ("111111111111111111111", "b.zone-1.example.com.|TXT|111111111111111111111"),
        ("2222222222222222222", "a.zone-2.example.com.|TXT|2222222222222222222"),
    }
    assert check_rels(
        neo4j_session,
        "GCPProject",
        "id",
        "GCPRecordSet",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (TEST_PROJECT_NUMBER, "a.zone-1.example.com.|TXT|111111111111111111111"),
        (TEST_PROJECT_NUMBER, "b.zone-1.example.com.|TXT|111111111111111111111"),
        (TEST_PROJECT_NUMBER, "a.zone-2.example.com.|TXT|2222222222222222222"),
    }
    assert check_rels(
        neo4j_session,
        "GCPProject",
        "id",
        "GCPRecordSet",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (TEST_PROJECT_ID, "a.zone-1.example.com.|TXT|111111111111111111111"),
        (TEST_PROJECT_ID, "b.zone-1.example.com.|TXT|111111111111111111111"),
        (TEST_PROJECT_ID, "a.zone-2.example.com.|TXT|2222222222222222222"),
    }
