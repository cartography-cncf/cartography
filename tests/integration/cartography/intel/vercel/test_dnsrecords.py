from unittest.mock import patch

import requests

import cartography.intel.vercel.dnsrecords
import tests.data.vercel.dnsrecords
from tests.integration.cartography.intel.vercel.test_domains import (
    _ensure_local_neo4j_has_test_domains,
)
from tests.integration.cartography.intel.vercel.test_teams import (
    _ensure_local_neo4j_has_test_teams,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_TEAM_ID = "team_abc123"
TEST_BASE_URL = "https://api.fake-vercel.com"
TEST_DOMAIN_NAME = "example.com"


def _ensure_local_neo4j_has_test_dns_records(neo4j_session):
    cartography.intel.vercel.dnsrecords.load_dns_records(
        neo4j_session,
        tests.data.vercel.dnsrecords.VERCEL_DNS_RECORDS,
        TEST_TEAM_ID,
        TEST_DOMAIN_NAME,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.vercel.dnsrecords,
    "get",
    return_value=tests.data.vercel.dnsrecords.VERCEL_DNS_RECORDS,
)
def test_load_vercel_dns_records(mock_api, neo4j_session):
    """
    Ensure that DNS records actually get loaded and linked to their domain
    """

    # Arrange
    api_session = requests.Session()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "BASE_URL": TEST_BASE_URL,
        "TEAM_ID": TEST_TEAM_ID,
        "domain_name": TEST_DOMAIN_NAME,
    }
    _ensure_local_neo4j_has_test_teams(neo4j_session)
    _ensure_local_neo4j_has_test_domains(neo4j_session)

    # Act
    cartography.intel.vercel.dnsrecords.sync(
        neo4j_session,
        api_session,
        common_job_parameters,
        domain_name=TEST_DOMAIN_NAME,
    )

    # Assert DNS Records exist
    expected_nodes = {
        ("rec_123",),
        ("rec_456",),
    }
    assert check_nodes(neo4j_session, "VercelDNSRecord", ["id"]) == expected_nodes

    # Assert DNS Records are connected to Team via RESOURCE (Team -RESOURCE-> DNSRecord)
    expected_team_rels = {
        ("rec_123", TEST_TEAM_ID),
        ("rec_456", TEST_TEAM_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "VercelDNSRecord",
            "id",
            "VercelTeam",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_team_rels
    )

    # Assert DNS Records are connected to Domain via HAS_DNS_RECORD
    # (Domain -HAS_DNS_RECORD-> DNSRecord)
    expected_domain_rels = {
        ("rec_123", TEST_DOMAIN_NAME),
        ("rec_456", TEST_DOMAIN_NAME),
    }
    assert (
        check_rels(
            neo4j_session,
            "VercelDNSRecord",
            "id",
            "VercelDomain",
            "id",
            "HAS_DNS_RECORD",
            rel_direction_right=False,
        )
        == expected_domain_rels
    )
