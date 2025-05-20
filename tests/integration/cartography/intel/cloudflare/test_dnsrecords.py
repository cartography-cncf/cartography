from unittest.mock import patch

import cartography.intel.cloudflare.dnsrecords
import tests.data.cloudflare.dnsrecords
import tests.data.cloudflare.zones
from tests.integration.cartography.intel.cloudflare.test_zones import (
    _ensure_local_neo4j_has_test_zones,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
ZONE_ID = tests.data.cloudflare.zones.CLOUDFLARE_ZONES[0]["id"]


@patch.object(
    cartography.intel.cloudflare.dnsrecords,
    "get",
    return_value=tests.data.cloudflare.dnsrecords.CLOUDFLARE_DNSRECORDS,
)
@patch("cloudflare.Cloudflare")
def test_load_cloudflare_dnsrecords(mock_cloudflare, mock_api, neo4j_session):
    """
    Ensure that dnsrecords actually get loaded
    """

    # Arrange
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "zone_id": ZONE_ID,
    }
    _ensure_local_neo4j_has_test_zones(neo4j_session)

    # Act
    cartography.intel.cloudflare.dnsrecords.sync(
        neo4j_session,
        mock_cloudflare,
        common_job_parameters,
        ZONE_ID,
    )

    # Assert DNSRecords exist
    expected_nodes = {
        (
            "2b534a38-8658-48c0-8d6d-f9277d689c75",
            "simpson.corp",
            "A",
            "1.2.3.4",
        ),
        (
            "922f7919-e12b-4f46-800f-74b433724d29",
            "www.simpson.corp",
            "CNAME",
            "simpson.corp",
        ),
    }
    assert (
        check_nodes(
            neo4j_session, "CloudflareDNSRecord", ["id", "name", "type", "value"]
        )
        == expected_nodes
    )

    # Assert DNSRecords are connected with Zone
    expected_rels = {
        ("2b534a38-8658-48c0-8d6d-f9277d689c75", ZONE_ID),
        ("922f7919-e12b-4f46-800f-74b433724d29", ZONE_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "CloudflareDNSRecord",
            "id",
            "CloudflareZone",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_rels
    )
