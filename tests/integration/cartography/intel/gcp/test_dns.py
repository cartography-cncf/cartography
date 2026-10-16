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
def test_sync_dns_zone_labels(_mock_get_zones, _mock_get_rrs, neo4j_session):
    """Test sync() loads GCPLabel nodes for DNS zones with labels."""
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _create_test_project(neo4j_session, TEST_PROJECT_ID, TEST_UPDATE_TAG)

    cartography.intel.gcp.dns.sync(
        neo4j_session,
        MagicMock(),
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        COMMON_JOB_PARAMS,
    )

    # Only test-zone-1 has labels
    assert check_nodes(neo4j_session, "GCPLabel", ["key", "value"]) == {
        ("env", "prod"),
        ("team", "networking"),
    }

    assert check_rels(
        neo4j_session,
        "GCPDNSZone",
        "id",
        "GCPLabel",
        "id",
        "LABELED",
        rel_direction_right=True,
    ) == {
        ("111111111111111111111", "111111111111111111111:env:prod"),
        ("111111111111111111111", "111111111111111111111:team:networking"),
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
def test_sync_removes_stale_legacy_record_sets_in_owned_zones(
    _mock_get_zones, _mock_get_rrs, neo4j_session
):
    """Record sets from before the data model migration have no RESOURCE edge, so only the
    legacy cleanup can remove them. It must not touch zones that this project does not own.
    """
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _create_test_project(neo4j_session, TEST_PROJECT_ID, TEST_UPDATE_TAG)
    cartography.intel.gcp.dns.sync(
        neo4j_session,
        MagicMock(),
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        COMMON_JOB_PARAMS,
    )
    # Legacy loaders wrote record sets with the record name as the id and only a HAS_RECORD
    # edge from the zone.
    neo4j_session.run(
        """
        MATCH (owned:GCPDNSZone{id: '111111111111111111111'})
        MERGE (other_project:GCPProject{id: 'other-project'})
        MERGE (other_project)-[:RESOURCE]->(other_zone:GCPDNSZone{id: 'other-zone'})
        MERGE (orphan_zone:GCPDNSZone{id: 'orphan-zone'})
        MERGE (owned)-[:HAS_RECORD]->(:GCPRecordSet{id: 'legacy.zone-1.example.com.', lastupdated: 1})
        MERGE (other_zone)-[:HAS_RECORD]->(:GCPRecordSet{id: 'legacy.other.example.com.', lastupdated: 1})
        MERGE (orphan_zone)-[:HAS_RECORD]->(:GCPRecordSet{id: 'legacy.orphan.example.com.', lastupdated: 1})
        MERGE (owned)-[:HAS_RECORD]->(shared:GCPRecordSet{id: 'legacy.shared.example.com.', lastupdated: 1})
        MERGE (other_zone)-[:HAS_RECORD]->(shared)
        """,
    )
    new_update_tag = TEST_UPDATE_TAG + 1

    # Act
    cartography.intel.gcp.dns.sync(
        neo4j_session,
        MagicMock(),
        TEST_PROJECT_ID,
        new_update_tag,
        {"UPDATE_TAG": new_update_tag, "PROJECT_ID": TEST_PROJECT_ID},
    )

    # Assert
    assert check_nodes(neo4j_session, "GCPRecordSet", ["id"]) == {
        ("a.zone-1.example.com.|TXT|111111111111111111111",),
        ("b.zone-1.example.com.|TXT|111111111111111111111",),
        ("a.zone-2.example.com.|TXT|2222222222222222222",),
        ("legacy.other.example.com.",),
        ("legacy.orphan.example.com.",),
        ("legacy.shared.example.com.",),
    }
    # A record set that another project's zone still references stays, detached from ours.
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
        ("other-zone", "legacy.other.example.com."),
        ("other-zone", "legacy.shared.example.com."),
        ("orphan-zone", "legacy.orphan.example.com."),
    }
