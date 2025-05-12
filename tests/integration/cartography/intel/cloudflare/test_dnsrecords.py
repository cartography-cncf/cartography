from unittest.mock import patch

import requests

import cartography.intel.cloudflare.dnsrecords
import tests.data.cloudflare.dnsrecords
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


@patch.object(cartography.cloudflare.dnsrecords, 'get', return_value=tests.data.cloudflare.dnsrecords.CLOUDFLARE_CLOUDFLARES)
def test_load_cloudflare_dnsrecords(mock_api, neo4j_session):
    """
    Ensure that dnsrecords actually get loaded
    """

    # Arrange
    api_session = requests.Session()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "BASE_URL": "https://fake.cloudflare.com",
    }
    zone_id = 'CHANGEME'  # CHANGEME: Add here expected parent id node

    # Act
    cartography.intel.cloudflare.dnsrecords.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
        zone_id,
    )

    # Assert DNSRecords exist
    expected_nodes = {
        # CHANGEME: Add here expected node from data
        # (123456, 'john.doe@domain.tld'),
    }
    assert check_nodes(
        neo4j_session,
        'CloudflareDNSRecord',
        ['id', 'email']
    ) == expected_nodes

    # Assert DNSRecords are connected with Zone
    expected_rels = {
        ('CHANGE_ME', zone_id),  # CHANGEME: Add here one of DNSRecords id
    }
    assert check_rels(
        neo4j_session,
        'CloudflareDNSRecord', 'id',
        'CloudflareZone', 'id',
        'RESOURCE',
        rel_direction_right=True,
    ) == expected_rels
