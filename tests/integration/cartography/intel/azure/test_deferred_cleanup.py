from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.azure as azure
from cartography.config import Config
from cartography.graph.job import GraphJob
from tests.data.azure.management_groups import AZURE_MANAGEMENT_GROUP_SUBSCRIPTIONS
from tests.data.azure.management_groups import AZURE_MANAGEMENT_GROUPS
from tests.data.azure.management_groups import TEST_CHILD_MANAGEMENT_GROUP_ID
from tests.data.azure.management_groups import TEST_SUBSCRIPTION_ID
from tests.data.azure.management_groups import TEST_TENANT_ID
from tests.integration import settings
from tests.integration.util import check_nodes

TEST_UPDATE_TAG = 123456789
TEST_UPDATE_TAG_V2 = 123456790


def _make_config(update_tag: int) -> Config:
    return Config(
        neo4j_uri=settings.get("NEO4J_URL"),
        update_tag=update_tag,
        azure_sync_all_subscriptions=True,
    )


def _make_credentials() -> MagicMock:
    credentials = MagicMock()
    credentials.tenant_id = TEST_TENANT_ID
    return credentials


def _make_subscription() -> dict:
    return {
        "id": f"/subscriptions/{TEST_SUBSCRIPTION_ID}",
        "subscriptionId": TEST_SUBSCRIPTION_ID,
        "displayName": "Test Subscription",
        "state": "Enabled",
    }


@patch("cartography.intel.azure.run_scoped_analysis_job")
@patch("cartography.intel.azure.run_analysis_job")
@patch("cartography.intel.azure._sync_one_subscription")
@patch("cartography.intel.azure.subscription.get_all_azure_subscriptions")
@patch("cartography.intel.azure.subscription.get_azure_management_group_subscriptions")
@patch("cartography.intel.azure.management_groups.get_azure_management_groups")
@patch("cartography.intel.azure.Authenticator.authenticate_cli")
def test_deferred_hierarchy_cleanup_order(
    mock_authenticate_cli,
    mock_get_management_groups,
    mock_get_management_group_subscriptions,
    mock_get_all_subscriptions,
    mock_sync_one_subscription,
    mock_run_analysis_job,
    mock_run_scoped_analysis_job,
    neo4j_session,
):
    mock_authenticate_cli.return_value = _make_credentials()
    mock_get_management_groups.return_value = AZURE_MANAGEMENT_GROUPS
    mock_get_management_group_subscriptions.return_value = (
        AZURE_MANAGEMENT_GROUP_SUBSCRIPTIONS,
        set(),
    )
    mock_get_all_subscriptions.return_value = [_make_subscription()]

    cleanup_order = []
    original_run = GraphJob.run

    def track_cleanup(self, session):
        if hasattr(self, "name"):
            cleanup_order.append(self.name)
        return original_run(self, session)

    with patch.object(GraphJob, "run", track_cleanup):
        azure.start_azure_ingestion(neo4j_session, _make_config(TEST_UPDATE_TAG))

    subscription_cleanup_idx = next(
        i for i, name in enumerate(cleanup_order) if "AzureSubscription" in name
    )
    management_group_cleanup_idx = next(
        i for i, name in enumerate(cleanup_order) if "AzureManagementGroup" in name
    )
    assert subscription_cleanup_idx < management_group_cleanup_idx


@patch("cartography.intel.azure.run_scoped_analysis_job")
@patch("cartography.intel.azure.run_analysis_job")
@patch("cartography.intel.azure._sync_one_subscription")
@patch("cartography.intel.azure.subscription.get_all_azure_subscriptions")
@patch("cartography.intel.azure.subscription.get_azure_management_group_subscriptions")
@patch("cartography.intel.azure.management_groups.get_azure_management_groups")
@patch("cartography.intel.azure.Authenticator.authenticate_cli")
def test_management_group_cleanup_skipped_after_management_group_access_loss(
    mock_authenticate_cli,
    mock_get_management_groups,
    mock_get_management_group_subscriptions,
    mock_get_all_subscriptions,
    mock_sync_one_subscription,
    mock_run_analysis_job,
    mock_run_scoped_analysis_job,
    neo4j_session,
):
    mock_authenticate_cli.return_value = _make_credentials()
    mock_get_management_groups.side_effect = [
        AZURE_MANAGEMENT_GROUPS,
        RuntimeError("management group enumeration failed"),
    ]
    mock_get_management_group_subscriptions.side_effect = [
        (AZURE_MANAGEMENT_GROUP_SUBSCRIPTIONS, set()),
        ([], set()),
    ]
    mock_get_all_subscriptions.return_value = [_make_subscription()]

    azure.start_azure_ingestion(neo4j_session, _make_config(TEST_UPDATE_TAG))
    azure.start_azure_ingestion(neo4j_session, _make_config(TEST_UPDATE_TAG_V2))

    management_group_nodes = check_nodes(
        neo4j_session,
        "AzureManagementGroup",
        ["id"],
    )
    assert (TEST_CHILD_MANAGEMENT_GROUP_ID,) in management_group_nodes
