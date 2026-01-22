from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.gcp.dns
import tests.data.gcp.dns
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_PROJECT_ID = "000000000000"
TEST_UPDATE_TAG = 123456789
COMMON_JOB_PARAMS = {
    "UPDATE_TAG": TEST_UPDATE_TAG,
    "PROJECT_ID": TEST_PROJECT_ID,
}


def _create_test_project(neo4j_session, project_id: str, update_tag: int):
    """Helper to create a GCPProject node for testing."""
    neo4j_session.run(
        """
        MERGE (p:GCPProject{id:$ProjectId})
        ON CREATE SET p.firstseen = timestamp()
        SET p.lastupdated = $gcp_update_tag
        """,
        ProjectId=project_id,
        gcp_update_tag=update_tag,
    )


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
def test_sync_dns_zones(_mock_get_zones, _mock_get_rrs, neo4j_session):
    """Test sync() loads DNS zones correctly."""
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _create_test_project(neo4j_session, TEST_PROJECT_ID, TEST_UPDATE_TAG)

    cartography.intel.gcp.dns.sync(
        neo4j_session,
        MagicMock(),
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        COMMON_JOB_PARAMS,
    )

    # Verify DNS zone nodes
    assert check_nodes(
        neo4j_session,
        "GCPDNSZone",
        ["id", "name"],
    ) == {
        ("111111111111111111111", "test-zone-1"),
        ("2222222222222222222", "test-zone-2"),
    }


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
def test_sync_dns_record_sets(_mock_get_zones, _mock_get_rrs, neo4j_session):
    """Test sync() loads DNS record sets correctly."""
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _create_test_project(neo4j_session, TEST_PROJECT_ID, TEST_UPDATE_TAG)

    cartography.intel.gcp.dns.sync(
        neo4j_session,
        MagicMock(),
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        COMMON_JOB_PARAMS,
    )

    # Verify DNS record set nodes
    assert check_nodes(
        neo4j_session,
        "GCPRecordSet",
        ["id"],
    ) == {
        ("a.zone-1.example.com.|TXT|111111111111111111111",),
        ("b.zone-1.example.com.|TXT|111111111111111111111",),
        ("a.zone-2.example.com.|TXT|2222222222222222222",),
    }


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
def test_sync_dns_zone_relationships(_mock_get_zones, _mock_get_rrs, neo4j_session):
    """Test sync() creates correct relationships for DNS zones."""
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _create_test_project(neo4j_session, TEST_PROJECT_ID, TEST_UPDATE_TAG)

    cartography.intel.gcp.dns.sync(
        neo4j_session,
        MagicMock(),
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        COMMON_JOB_PARAMS,
    )

    # Verify project -> zone RESOURCE relationship
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
def test_sync_dns_record_set_relationships(
    _mock_get_zones, _mock_get_rrs, neo4j_session
):
    """Test sync() creates correct relationships for DNS record sets."""
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _create_test_project(neo4j_session, TEST_PROJECT_ID, TEST_UPDATE_TAG)

    cartography.intel.gcp.dns.sync(
        neo4j_session,
        MagicMock(),
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        COMMON_JOB_PARAMS,
    )

    # Verify zone -> record set HAS_RECORD relationship
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

    # Verify project -> record set RESOURCE relationship
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
