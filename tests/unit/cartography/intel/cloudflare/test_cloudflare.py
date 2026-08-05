from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

import cartography.intel.cloudflare
from cartography.config import Config
from cartography.intel.cloudflare import start_cloudflare_ingestion

TEST_UPDATE_TAG = 123456789
ACCOUNT_ID = "37418d7e-710b-4aa0-a4c0-79ee660690bf"
ZONE_ID = "be68b067-5b2b-49f7-ad89-943d501dc900"


def test_start_cloudflare_ingestion_requires_token():
    config = Config(neo4j_uri="bolt://localhost:7687")

    with pytest.raises(RuntimeError, match="Cloudflare import is not configured"):
        start_cloudflare_ingestion(None, config)


@patch.object(cartography.intel.cloudflare.rulesets, "sync")
@patch.object(cartography.intel.cloudflare.workerroutes, "sync")
@patch.object(cartography.intel.cloudflare.workerscripts, "sync")
@patch.object(cartography.intel.cloudflare.r2buckets, "get", return_value=([], False))
@patch.object(cartography.intel.cloudflare.dnsrecords, "sync")
@patch.object(cartography.intel.cloudflare.dnsrecords, "migrate_account_resource_edges")
@patch.object(
    cartography.intel.cloudflare.zones, "sync", return_value=[{"id": ZONE_ID}]
)
@patch.object(cartography.intel.cloudflare.members, "sync")
@patch.object(cartography.intel.cloudflare.roles, "sync")
@patch.object(
    cartography.intel.cloudflare.accounts, "sync", return_value=[{"id": ACCOUNT_ID}]
)
@patch("cartography.intel.cloudflare.Cloudflare")
def test_r2_listing_failure_does_not_stop_the_later_stages(
    mock_client_class,
    mock_accounts,
    mock_roles,
    mock_members,
    mock_zones,
    mock_migrate,
    mock_dnsrecords,
    mock_r2_get,
    mock_workerscripts,
    mock_workerroutes,
    mock_rulesets,
):
    """
    Ensure that a refused R2 bucket listing does not abort the ingestion: the
    Workers and ruleset stages still run, as the module config documents.
    """

    # Arrange
    config = Config(
        neo4j_uri="bolt://localhost:7687",
        cloudflare_token="fake-token",
        update_tag=TEST_UPDATE_TAG,
    )

    # Act: r2buckets.sync runs for real and returns early on the failed listing
    start_cloudflare_ingestion(MagicMock(), config)

    # Assert the stages that come after R2 still ran
    mock_r2_get.assert_called_once()
    mock_workerscripts.assert_called_once()
    mock_workerroutes.assert_called_once()
    mock_rulesets.assert_called_once()
