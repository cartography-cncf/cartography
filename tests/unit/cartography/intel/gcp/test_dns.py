from unittest.mock import MagicMock, patch
import cartography.intel.gcp.dns
from cartography.intel.gcp.dns import sync
import tests.data.gcp.dns
from tests.integration.conftest import neo4j_session
from tests.integration.util import check_nodes, check_rels

TEST_PROJECT_ID = "project-x"
TEST_UPDATE_TAG = 123456789
TEST_AUTH = "test-auth"


def create_test_project(neo4j_session, project_id: str, update_tag: int) -> None:
    """Create a test GCP project for testing relationships."""
    neo4j_session.run(
        """
        MERGE (project:GCPProject {id: $project_id})
        SET project.lastupdated = $update_tag 
        """,
        project_id=project_id,
        update_tag=update_tag,
    )


def create_test_gcp_resources(neo4j_session) -> None:
    """Create test GCP resources for DNS relationship testing."""
    # Create test instance
    neo4j_session.run(
        """
        MERGE (instance:GCPInstance {
            id: "test-instance-1", 
            name: "web-server-1",
            external_ip: "203.0.113.1"
        })
        SET instance.lastupdated = $update_tag
        """,
        update_tag=TEST_UPDATE_TAG,
    )
    
    # Create test load balancer
    neo4j_session.run(
        """
        MERGE (lb:GCPLoadBalancer {
            id: "test-lb-1",
            name: "main-lb",
            ip_address: "203.0.113.100"
        })
        SET lb.lastupdated = $update_tag
        """,
        update_tag=TEST_UPDATE_TAG,
    )


def create_stale_dns_data(neo4j_session, old_update_tag: int) -> None:
    """Create stale DNS data for cleanup testing."""
    neo4j_session.run(
        """
        CREATE (z:GCPDNSZone {
            id: 'stale-zone', 
            name: 'stale-zone',
            dns_name: 'stale.example.com.',
            lastupdated: $old_update_tag
        })
        CREATE (r:GCPRecordSet {
            id: 'stale-record', 
            name: 'stale-record.example.com.',
            type: 'A',
            lastupdated: $old_update_tag
        })
        """,
        old_update_tag=old_update_tag,
    )


def get_common_job_parameters() -> dict:
    """Get standard job parameters for testing."""
    return {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "project_id": TEST_PROJECT_ID,
    }


class TestGCPDNSSync:
    """Test suite for GCP DNS synchronization functionality."""

    @patch.object(
        cartography.intel.gcp.dns,
        "get_dns_zones",
        return_value=tests.data.gcp.dns.DNS_ZONES,
    )
    @patch.object(
        cartography.intel.gcp.dns,
        "get_dns_rrs",
        return_value=tests.data.gcp.dns.DNS_RRS,
    )
    def test_sync_creates_expected_nodes(self, mock_get_rrs, mock_get_zones, neo4j_session):
        """Test that DNS sync creates the expected GCPDNSZone and GCPRecordSet nodes."""
        # Arrange
        neo4j_session.run("MATCH (n) DETACH DELETE n")
        gcp_client = MagicMock()
        create_test_project(neo4j_session, TEST_PROJECT_ID, TEST_UPDATE_TAG)

        # Act
        cartography.intel.gcp.dns.sync(
            neo4j_session,
            gcp_client,
            TEST_PROJECT_ID,
            TEST_UPDATE_TAG,
            get_common_job_parameters(),
        )

        # Assert - Verify DNS zones
        expected_zones = {
            ("111111111111111111111", "zone-1.example.com."),
            ("2222222222222222222", "zone-2.example.com."),
        }
        actual_zones = check_nodes(neo4j_session, "GCPDNSZone", ["id", "dns_name"])
        assert actual_zones == expected_zones

        # Assert - Verify DNS records
        expected_records = {
            ("a.zone-1.example.com.", "a.zone-1.example.com.", "TXT"),
            ("b.zone-1.example.com.", "b.zone-1.example.com.", "TXT"),
            ("a.zone-2.example.com.", "a.zone-2.example.com.", "TXT"),
        }
        actual_records = check_nodes(neo4j_session, "GCPRecordSet", ["id", "name", "type"])
        assert actual_records == expected_records

    @patch.object(
        cartography.intel.gcp.dns,
        "get_dns_zones",
        return_value=tests.data.gcp.dns.DNS_ZONES,
    )
    @patch.object(
        cartography.intel.gcp.dns,
        "get_dns_rrs",
        return_value=tests.data.gcp.dns.DNS_RRS,
    )
    def test_sync_creates_proper_relationships(self, mock_get_rrs, mock_get_zones, neo4j_session):
        """Test that DNS sync creates proper relationships between zones, records, and projects."""
        # Arrange
        neo4j_session.run("MATCH (n) DETACH DELETE n")
        gcp_client = MagicMock()
        create_test_project(neo4j_session, TEST_PROJECT_ID, TEST_UPDATE_TAG)

        # Act
        sync(
            neo4j_session,
            gcp_client,
            TEST_PROJECT_ID,
            TEST_UPDATE_TAG,
            get_common_job_parameters(),
        )

        # Assert - Verify project to zone relationships
        expected_zone_project_rels = {
            (TEST_PROJECT_ID, "111111111111111111111"),
            (TEST_PROJECT_ID, "2222222222222222222"),
        }
        actual_zone_project_rels = check_rels(
            neo4j_session,
            "GCPProject", "id",
            "GCPDNSZone", "id",
            "RESOURCE",
            rel_direction_right=True,
        )
        assert actual_zone_project_rels == expected_zone_project_rels

        # Assert - Verify zone to record relationships
        expected_record_zone_rels = {
            ("111111111111111111111", "a.zone-1.example.com."),
            ("111111111111111111111", "b.zone-1.example.com."),
            ("2222222222222222222", "a.zone-2.example.com."),
        }
        actual_record_zone_rels = check_rels(
            neo4j_session,
            "GCPDNSZone", "id",
            "GCPRecordSet", "id",
            "HAS_RECORD",  
            rel_direction_right=True,
        )
        assert actual_record_zone_rels == expected_record_zone_rels

    @patch.object(
        cartography.intel.gcp.dns, 
        "get_dns_zones", 
        return_value=tests.data.gcp.dns.DNS_ZONES
    )
    @patch.object(
        cartography.intel.gcp.dns, 
        "get_dns_rrs", 
        return_value=tests.data.gcp.dns.DNS_RRS
    )
    def test_sync_with_existing_gcp_resources(self, mock_get_rrs, mock_get_zones, neo4j_session):
        """Test DNS sync behavior when other GCP resources already exist."""
        # Arrange
        gcp_client = MagicMock()
        create_test_project(neo4j_session, TEST_PROJECT_ID, TEST_UPDATE_TAG)
        create_test_gcp_resources(neo4j_session)

        # Act
        sync(
            neo4j_session, 
            gcp_client, 
            TEST_PROJECT_ID, 
            TEST_UPDATE_TAG, 
            get_common_job_parameters()
        )

        # Assert - Verify no unexpected DNS_POINTS_TO relationships
        instance_dns_rels = check_rels(
            neo4j_session, 
            "GCPRecordSet", "id", 
            "GCPInstance", "id", 
            "DNS_POINTS_TO", 
            rel_direction_right=True
        )
        assert instance_dns_rels == set()

        lb_dns_rels = check_rels(
            neo4j_session, 
            "GCPRecordSet", "id", 
            "GCPLoadBalancer", "id", 
            "DNS_POINTS_TO", 
            rel_direction_right=True
        )
        assert lb_dns_rels == set()

    @patch.object(
        cartography.intel.gcp.dns, 
        "get_dns_zones", 
        return_value=tests.data.gcp.dns.DNS_ZONES
    )
    @patch.object(
        cartography.intel.gcp.dns, 
        "get_dns_rrs", 
        return_value=tests.data.gcp.dns.DNS_RRS
    )
    def test_sync_cleanup_removes_stale_data(self, mock_get_rrs, mock_get_zones, neo4j_session):
        """Test that sync properly removes stale DNS data during cleanup."""
        # Arrange
        gcp_client = MagicMock()
        create_test_project(neo4j_session, TEST_PROJECT_ID, TEST_UPDATE_TAG)
        
        old_update_tag = TEST_UPDATE_TAG - 1000
        create_stale_dns_data(neo4j_session, old_update_tag)

        # Act
        cartography.intel.gcp.dns.sync(
            neo4j_session,
            gcp_client,
            TEST_PROJECT_ID,
            TEST_UPDATE_TAG,
            get_common_job_parameters(),
        )

        # Assert - Verify stale zones are removed
        all_zones = check_nodes(neo4j_session, "GCPDNSZone", ["id"])
        zone_ids = {zone[0] for zone in all_zones}
        assert "stale-zone" not in zone_ids

        # Assert - Verify stale records are removed
        all_records = check_nodes(neo4j_session, "GCPRecordSet", ["id"])
        record_ids = {record[0] for record in all_records}
        assert "stale-record" not in record_ids

    @patch.object(
        cartography.intel.gcp.dns, 
        "get_dns_zones", 
        return_value=tests.data.gcp.dns.DNS_ZONES
    )
    @patch.object(
        cartography.intel.gcp.dns, 
        "get_dns_rrs", 
        return_value=tests.data.gcp.dns.DNS_RRS
    )
    def test_sync_record_to_record_relationships(self, mock_get_rrs, mock_get_zones, neo4j_session):
        """Test DNS record to record relationships (e.g., CNAME resolution)."""
        # Arrange
        gcp_client = MagicMock()
        create_test_project(neo4j_session, TEST_PROJECT_ID, TEST_UPDATE_TAG)

        # Act
        sync(
            neo4j_session, 
            gcp_client, 
            TEST_PROJECT_ID, 
            TEST_UPDATE_TAG, 
            get_common_job_parameters()
        )

        # Assert - Verify record-to-record relationships
        actual_record_rels = check_rels(
            neo4j_session,
            "GCPRecordSet", "id",
            "GCPRecordSet", "id",
            "DNS_POINTS_TO",
            rel_direction_right=True,
        )
        assert actual_record_rels == set()

    @patch.object(
        cartography.intel.gcp.dns, 
        "get_dns_zones", 
        return_value=tests.data.gcp.dns.DNS_ZONES
    )
    @patch.object(
        cartography.intel.gcp.dns, 
        "get_dns_rrs", 
        return_value=tests.data.gcp.dns.DNS_RRS
    )
    def test_sync_idempotency(self, mock_get_rrs, mock_get_zones, neo4j_session):
        """Test that running sync multiple times produces consistent results."""
        # Arrange
        gcp_client = MagicMock()
        create_test_project(neo4j_session, TEST_PROJECT_ID, TEST_UPDATE_TAG)

        # Act - Run sync twice with different update tags
        sync(
            neo4j_session,
            gcp_client,
            TEST_PROJECT_ID,
            TEST_UPDATE_TAG,
            {"UPDATE_TAG": TEST_UPDATE_TAG, "project_id": TEST_PROJECT_ID},
        )
        sync(
            neo4j_session,
            gcp_client,
            TEST_PROJECT_ID,
            TEST_UPDATE_TAG + 1,
            {"UPDATE_TAG": TEST_UPDATE_TAG + 1, "project_id": TEST_PROJECT_ID},
        )

        # Assert - Verify consistent node counts
        zones = check_nodes(neo4j_session, "GCPDNSZone", ["id"])
        records = check_nodes(neo4j_session, "GCPRecordSet", ["id"])
        
        assert len(zones) == 2
        assert len(records) == 3


class TestGCPDNSLoaders:
    """Test suite for individual DNS loader functions."""

    def test_load_dns_zones_basic(self, neo4j_session):
        """Test basic DNS zone loading functionality."""
        # Arrange
        create_test_project(neo4j_session, TEST_PROJECT_ID, TEST_UPDATE_TAG)

        # Act
        cartography.intel.gcp.dns.load_dns_zones(
            neo4j_session,
            tests.data.gcp.dns.DNS_ZONES,
            TEST_PROJECT_ID,
            TEST_UPDATE_TAG,
        )

        # Assert
        zones = check_nodes(neo4j_session, "GCPDNSZone", ["id"])
        assert len(zones) == 2

    def test_load_dns_records_basic(self, neo4j_session):
        """Test basic DNS record loading functionality."""
        # Arrange
        create_test_project(neo4j_session, TEST_PROJECT_ID, TEST_UPDATE_TAG)
        
        # Load zones first (required for records)
        cartography.intel.gcp.dns.load_dns_zones(
            neo4j_session,
            tests.data.gcp.dns.DNS_ZONES,
            TEST_PROJECT_ID,
            TEST_UPDATE_TAG,
        )

        # Act
        cartography.intel.gcp.dns.load_rrs(
            neo4j_session,
            tests.data.gcp.dns.DNS_RRS,
            TEST_PROJECT_ID,
            TEST_UPDATE_TAG,
        )

        # Assert
        records = check_nodes(neo4j_session, "GCPRecordSet", ["id"])
        assert len(records) == 3