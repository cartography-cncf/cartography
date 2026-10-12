from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

import cartography.intel.azure as azure
from cartography.config import Config
from cartography.intel.azure.resources import RESOURCE_FUNCTIONS
from cartography.intel.azure.util.common import parse_and_validate_azure_requested_syncs

TEST_TENANT_ID = "00000000-0000-0000-0000-000000000001"
TEST_SUBSCRIPTION_ID = "00000000-0000-0000-0000-000000000002"

# Every per-subscription sync entry point, keyed by the resource that gates it.
SUBSCRIPTION_SYNCS = {
    "compute": ["compute.sync"],
    "cosmosdb": ["cosmosdb.sync"],
    "app_service": ["app_service.sync"],
    "functions": ["functions.sync"],
    "event_grid": ["event_grid.sync"],
    "logic_apps": ["logic_apps.sync"],
    "rbac": ["rbac.sync"],
    "workload_identity": ["workload_identity.sync"],
    "sql": ["sql.sync"],
    "storage": ["storage.sync"],
    "resource_groups": ["resource_groups.sync"],
    "key_vaults": ["key_vaults.sync"],
    "aks": ["aks.sync"],
    "event_hub": [
        "event_hub_namespace.sync_event_hub_namespaces",
        "event_hub.sync_event_hubs",
    ],
    "data_factory": ["_sync_data_factory"],
    "data_lake": ["data_lake.sync"],
    "network": ["network.sync"],
    "container_instances": [
        "group_containers.sync_group_containers",
        "container_instances.sync",
    ],
    "firewall": ["firewall.sync"],
    "load_balancers": ["load_balancers.sync"],
    "application_gateways": ["application_gateways.sync"],
    "synapse": ["synapse.sync"],
    "monitor": ["monitor.sync"],
    "security_center": ["security_center.sync"],
    "permission_relationships": ["permission_relationships.sync"],
}


def _mock_subscription_syncs(monkeypatch) -> dict[str, MagicMock]:
    mocks = {}
    for targets in SUBSCRIPTION_SYNCS.values():
        for target in targets:
            mock = MagicMock()
            if "." in target:
                module_name, func_name = target.split(".")
                monkeypatch.setattr(getattr(azure, module_name), func_name, mock)
            else:
                monkeypatch.setattr(azure, target, mock)
            mocks[target] = mock
    return mocks


def _called_resources(mocks: dict[str, MagicMock]) -> set[str]:
    return {
        resource
        for resource, targets in SUBSCRIPTION_SYNCS.items()
        if any(mocks[target].called for target in targets)
    }


def test_parse_requested_syncs_strips_whitespace() -> None:
    # Act
    result = parse_and_validate_azure_requested_syncs("rbac, compute ,storage")

    # Assert
    assert result == ["rbac", "compute", "storage"]


def test_parse_requested_syncs_rejects_unknown_resource() -> None:
    # Act and assert
    with pytest.raises(ValueError, match="azure-requested-syncs"):
        parse_and_validate_azure_requested_syncs("rbac,virtual_machines")


def test_every_resource_gates_a_sync() -> None:
    # Assert
    assert set(RESOURCE_FUNCTIONS) == {*SUBSCRIPTION_SYNCS, "management_groups"}


def test_sync_one_subscription_runs_only_requested_resources(monkeypatch) -> None:
    # Arrange
    mocks = _mock_subscription_syncs(monkeypatch)

    # Act
    azure._sync_one_subscription(
        MagicMock(),
        MagicMock(),
        TEST_SUBSCRIPTION_ID,
        1234567890,
        {},
        {"rbac", "event_hub"},
    )

    # Assert
    called = {target for target, mock in mocks.items() if mock.called}
    assert called == {
        "rbac.sync",
        "event_hub_namespace.sync_event_hub_namespaces",
        "event_hub.sync_event_hubs",
    }


def test_sync_one_subscription_runs_everything_by_default(monkeypatch) -> None:
    # Arrange
    mocks = _mock_subscription_syncs(monkeypatch)

    # Act
    azure._sync_one_subscription(
        MagicMock(),
        MagicMock(),
        TEST_SUBSCRIPTION_ID,
        1234567890,
        {},
    )

    # Assert
    assert _called_resources(mocks) == set(SUBSCRIPTION_SYNCS)
    assert all(mock.called for mock in mocks.values())


@pytest.mark.parametrize(
    "requested, management_groups_run",
    [("rbac", False), ("rbac,management_groups", True)],
)
@patch("cartography.intel.azure.run_typed_analysis_job")
@patch("cartography.intel.azure.run_analysis_job")
@patch(
    "cartography.intel.azure.rbac.sync_management_group_role_assignments_for_management_groups"
)
@patch("cartography.intel.azure.management_groups.cleanup")
@patch("cartography.intel.azure._sync_management_groups")
@patch("cartography.intel.azure._sync_one_subscription")
@patch("cartography.intel.azure.subscription")
@patch("cartography.intel.azure.tenant")
@patch("cartography.intel.azure.Authenticator.authenticate_cli")
def test_management_groups_sync_only_when_requested(
    mock_authenticate_cli,
    mock_tenant,
    mock_subscription,
    mock_sync_one_subscription,
    mock_sync_management_groups,
    mock_management_groups_cleanup,
    mock_management_group_role_assignments,
    mock_run_analysis_job,
    mock_run_typed_analysis_job,
    requested,
    management_groups_run,
):
    # Arrange
    credentials = MagicMock(tenant_id=TEST_TENANT_ID)
    mock_authenticate_cli.return_value = credentials
    mock_subscription.get_all_azure_subscriptions.return_value = [
        {"subscriptionId": TEST_SUBSCRIPTION_ID},
    ]
    config = Config(
        neo4j_uri="bolt://localhost:7687",
        update_tag=1234567890,
        azure_sync_all_subscriptions=True,
        azure_requested_syncs=requested,
    )

    # Act
    azure.start_azure_ingestion(MagicMock(), config)

    # Assert
    mock_tenant.sync.assert_called_once()
    mock_subscription.sync.assert_called_once()
    assert mock_sync_management_groups.called is management_groups_run
    assert mock_management_group_role_assignments.called is management_groups_run
    assert mock_management_groups_cleanup.called is management_groups_run
    assert mock_sync_one_subscription.call_args.args[-1] == set(requested.split(","))
