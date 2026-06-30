from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.scaleway.dns.dns
from tests.data.scaleway.dns import SCALEWAY_DNS_RECORDS_BY_ZONE
from tests.data.scaleway.dns import SCALEWAY_DNS_ZONES
from tests.data.scaleway.dns import TEST_RECORD_A_ID
from tests.data.scaleway.dns import TEST_RECORD_MX_ID
from tests.data.scaleway.dns import TEST_ZONE_ID
from tests.integration.cartography.intel.scaleway.test_projects import (
    _ensure_local_neo4j_has_test_projects_and_orgs,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_ORG_ID = "0681c477-fbb9-4820-b8d6-0eef10cfcd6d"
TEST_PROJECT_ID = "0681c477-fbb9-4820-b8d6-0eef10cfcd6d"


@patch.object(
    cartography.intel.scaleway.dns.dns,
    "get",
    return_value=(SCALEWAY_DNS_ZONES, SCALEWAY_DNS_RECORDS_BY_ZONE),
)
def test_load_scaleway_dns(_mock_get, neo4j_session):
    # Arrange
    client = Mock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ORG_ID": TEST_ORG_ID,
    }
    _ensure_local_neo4j_has_test_projects_and_orgs(neo4j_session)

    # Act
    cartography.intel.scaleway.dns.dns.sync(
        neo4j_session,
        client,
        common_job_parameters,
        org_id=TEST_ORG_ID,
        projects_id=[TEST_PROJECT_ID],
        update_tag=TEST_UPDATE_TAG,
    )

    # Assert nodes
    assert check_nodes(neo4j_session, "ScalewayDnsZone", ["id", "domain"]) == {
        (TEST_ZONE_ID, "example-cartography.com"),
    }
    assert check_nodes(neo4j_session, "ScalewayDnsRecord", ["id", "type"]) == {
        (TEST_RECORD_A_ID, "a"),
        (TEST_RECORD_MX_ID, "mx"),
    }

    # Cross-cloud ontology labels
    assert check_nodes(neo4j_session, "DNSZone", ["id"]) == {(TEST_ZONE_ID,)}
    assert check_nodes(neo4j_session, "DNSRecord", ["id"]) == {
        (TEST_RECORD_A_ID,),
        (TEST_RECORD_MX_ID,),
    }

    # Project ownership
    for label in ("ScalewayDnsZone", "ScalewayDnsRecord"):
        assert check_rels(
            neo4j_session,
            label,
            "id",
            "ScalewayProject",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        ), f"{label} not linked to project"

    # Zone -> Records
    assert check_rels(
        neo4j_session,
        "ScalewayDnsZone",
        "id",
        "ScalewayDnsRecord",
        "id",
        "HAS_RECORD",
        rel_direction_right=True,
    ) == {
        (TEST_ZONE_ID, TEST_RECORD_A_ID),
        (TEST_ZONE_ID, TEST_RECORD_MX_ID),
    }
