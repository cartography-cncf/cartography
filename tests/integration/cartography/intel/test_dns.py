from unittest.mock import patch

import cartography.intel.dns
from cartography.client.core.tx import run_write_query
from tests.data.dns import RESOLVED_IPS
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_FQDN = "example.cartography.test"
TEST_PARENT_ID = "es-domain-001"
TEST_RECORD_LABEL = "ESDomain"
TEST_DNS_LABEL = "AWSDNSRecord"


def _create_parent_node(neo4j_session):
    run_write_query(
        neo4j_session,
        """
        MERGE (n:ESDomain{id: $Id})
        ON CREATE SET n.firstseen = timestamp()
        SET n.lastupdated = $update_tag
        """,
        Id=TEST_PARENT_ID,
        update_tag=TEST_UPDATE_TAG,
    )


@patch.object(cartography.intel.dns, "get_dns_record_type", return_value="A")
@patch.object(
    cartography.intel.dns, "get_dns_resolution_by_fqdn", return_value=RESOLVED_IPS
)
def test_ingest_dns_record_by_fqdn(mock_resolve, mock_type, neo4j_session):
    """
    Ensure that ingest_dns_record_by_fqdn() creates DNSRecord and Ip nodes with proper relationships.
    """
    _create_parent_node(neo4j_session)

    cartography.intel.dns.ingest_dns_record_by_fqdn(
        neo4j_session,
        TEST_UPDATE_TAG,
        TEST_FQDN,
        TEST_PARENT_ID,
        TEST_RECORD_LABEL,
        dns_node_additional_label=TEST_DNS_LABEL,
    )

    # Verify DNSRecord node
    assert check_nodes(neo4j_session, "DNSRecord", ["id", "name", "type", "value"]) == {
        (f"{TEST_FQDN}+A", TEST_FQDN, "A", "192.0.2.1,192.0.2.10"),
    }

    # Verify Ip nodes
    assert check_nodes(neo4j_session, "Ip", ["id"]) == {
        ("192.0.2.1",),
        ("192.0.2.10",),
    }

    # Verify DNSRecord -[:DNS_POINTS_TO]-> ESDomain
    assert check_rels(
        neo4j_session,
        "DNSRecord",
        "id",
        "ESDomain",
        "id",
        "DNS_POINTS_TO",
        rel_direction_right=True,
    ) == {
        (f"{TEST_FQDN}+A", TEST_PARENT_ID),
    }

    # Verify DNSRecord -[:DNS_POINTS_TO]-> Ip
    assert check_rels(
        neo4j_session,
        "DNSRecord",
        "id",
        "Ip",
        "id",
        "DNS_POINTS_TO",
        rel_direction_right=True,
    ) == {
        (f"{TEST_FQDN}+A", "192.0.2.1"),
        (f"{TEST_FQDN}+A", "192.0.2.10"),
    }
