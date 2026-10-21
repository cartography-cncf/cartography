from contextlib import ExitStack
from unittest.mock import MagicMock
from unittest.mock import patch

import httpx
import pytest
from cloudflare import APIConnectionError
from cloudflare import APIStatusError

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


@patch.object(cartography.intel.cloudflare.access, "sync")
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
    mock_access,
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
    mock_access.assert_called_once()


@pytest.mark.parametrize("failure", ["status", "connection"])
def test_access_listing_failure_does_not_stop_the_next_account(failure, caplog):
    # Arrange: run real Access sync, mocking only API reads and graph writes.
    accounts = [{"id": ACCOUNT_ID}, {"id": "second-account"}]
    zones = [{"id": ZONE_ID, "name": "example.com"}]
    records = [{"id": "record", "name": "app.example.com"}]
    request = httpx.Request(
        "GET", "https://api.cloudflare.com/client/v4/accounts/test/access/apps"
    )
    error = (
        APIConnectionError(request=request)
        if failure == "connection"
        else APIStatusError(
            "test failure", response=httpx.Response(500, request=request), body=None
        )
    )
    config = Config(
        neo4j_uri="bolt://localhost:7687",
        cloudflare_token="synthetic",
        update_tag=TEST_UPDATE_TAG,
    )
    with ExitStack() as stack:
        stack.enter_context(patch("cartography.intel.cloudflare.Cloudflare"))
        stack.enter_context(
            patch.object(
                cartography.intel.cloudflare.accounts, "sync", return_value=accounts
            )
        )
        stages = {}
        for name in (
            "roles",
            "members",
            "zones",
            "dnsrecords",
            "r2buckets",
            "workerscripts",
            "workerroutes",
            "rulesets",
        ):
            stages[name] = stack.enter_context(
                patch.object(getattr(cartography.intel.cloudflare, name), "sync")
            )
        stages["zones"].return_value = zones
        stages["dnsrecords"].return_value = records
        stack.enter_context(
            patch.object(
                cartography.intel.cloudflare.dnsrecords,
                "migrate_account_resource_edges",
            )
        )
        get_apps = stack.enter_context(
            patch.object(
                cartography.intel.cloudflare.access,
                "get_applications",
                side_effect=[error, []],
            )
        )
        load_apps = stack.enter_context(
            patch.object(cartography.intel.cloudflare.access, "load_applications")
        )
        stack.enter_context(
            patch.object(cartography.intel.cloudflare.access, "load_policies")
        )
        cleanup = stack.enter_context(
            patch.object(cartography.intel.cloudflare.access, "cleanup")
        )
        transform = stack.enter_context(
            patch.object(
                cartography.intel.cloudflare.access,
                "transform_applications",
                wraps=cartography.intel.cloudflare.access.transform_applications,
            )
        )
        session = MagicMock()

        # Act
        start_cloudflare_ingestion(session, config)

    # Assert: second-account ingestion proceeds and only its Access graph is touched.
    assert [call.args[1] for call in get_apps.call_args_list] == [
        ACCOUNT_ID,
        "second-account",
    ]
    assert all(stage.call_count == 2 for stage in stages.values())
    transform.assert_called_once_with([], "second-account", zones, records)
    load_apps.assert_called_once_with(session, [], "second-account", TEST_UPDATE_TAG)
    cleanup.assert_called_once_with(
        session, {"UPDATE_TAG": TEST_UPDATE_TAG, "account_id": "second-account"}
    )
    assert session.mock_calls == []
    assert "Skipping Access loading and cleanup" in caplog.text
