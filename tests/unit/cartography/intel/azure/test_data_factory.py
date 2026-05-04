from contextlib import ExitStack
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from azure.core.exceptions import HttpResponseError

import cartography.intel.azure as azure
import cartography.intel.azure.data_factory as data_factory
from cartography.intel.azure.data_factory_util import AzureDataFactoryTransientError


class _SyntheticHttpResponseError(HttpResponseError):
    def __init__(self, status_code: int) -> None:
        Exception.__init__(self, "synthetic")
        self._status_code = status_code

    @property
    def status_code(self) -> int:
        return self._status_code


class _AzureResource:
    def __init__(self, data: dict) -> None:
        self.data = data

    def as_dict(self) -> dict:
        return self.data


def test_get_factories_retries_transient_error() -> None:
    client = MagicMock()
    client.factories.list.side_effect = [
        _SyntheticHttpResponseError(503),
        [_AzureResource({"id": "factory-1"})],
    ]

    with patch("cartography.intel.azure.data_factory_util.time.sleep") as mock_sleep:
        result = data_factory.get_factories(client)

    assert result == [{"id": "factory-1"}]
    assert client.factories.list.call_count == 2
    mock_sleep.assert_called_once()


def test_sync_data_factories_raises_transient_error_without_cleanup() -> None:
    neo4j_session = MagicMock()
    credentials = MagicMock()

    with (
        patch(
            "cartography.intel.azure.data_factory.get_factories",
            side_effect=AzureDataFactoryTransientError(
                "list data factories",
                503,
            ),
        ),
        patch("cartography.intel.azure.data_factory.load_factories") as mock_load,
        patch(
            "cartography.intel.azure.data_factory.cleanup_data_factories"
        ) as mock_cleanup,
    ):
        with pytest.raises(AzureDataFactoryTransientError):
            data_factory.sync_data_factories(
                neo4j_session,
                credentials,
                "subscription-1",
                123,
                {"UPDATE_TAG": 123},
            )

    mock_load.assert_not_called()
    mock_cleanup.assert_not_called()


def test_get_factories_raises_transient_error_after_retry_exhaustion() -> None:
    client = MagicMock()
    client.factories.list.side_effect = [
        _SyntheticHttpResponseError(503),
        _SyntheticHttpResponseError(503),
        _SyntheticHttpResponseError(503),
    ]

    with (
        patch("cartography.intel.azure.data_factory_util.time.sleep") as mock_sleep,
        pytest.raises(AzureDataFactoryTransientError) as excinfo,
    ):
        data_factory.get_factories(client)

    assert excinfo.value.operation == "list data factories"
    assert excinfo.value.status_code == 503
    assert excinfo.value.__cause__ is None
    assert client.factories.list.call_count == 3
    assert mock_sleep.call_count == 2


def test_sync_one_subscription_skips_data_factory_subtree_after_transient_error() -> (
    None
):
    neo4j_session = MagicMock()
    credentials = MagicMock()
    credentials.credential = MagicMock()

    patches = [
        "cartography.intel.azure.compute.sync",
        "cartography.intel.azure.cosmosdb.sync",
        "cartography.intel.azure.app_service.sync",
        "cartography.intel.azure.functions.sync",
        "cartography.intel.azure.event_grid.sync",
        "cartography.intel.azure.logic_apps.sync",
        "cartography.intel.azure.rbac.sync",
        "cartography.intel.azure.sql.sync",
        "cartography.intel.azure.storage.sync",
        "cartography.intel.azure.resource_groups.sync",
        "cartography.intel.azure.key_vaults.sync",
        "cartography.intel.azure.aks.sync",
        "cartography.intel.azure.event_hub.sync_event_hubs",
        "cartography.intel.azure.network.sync",
        "cartography.intel.azure.group_containers.sync_group_containers",
        "cartography.intel.azure.container_instances.sync",
        "cartography.intel.azure.firewall.sync",
        "cartography.intel.azure.load_balancers.sync",
        "cartography.intel.azure.synapse.sync",
        "cartography.intel.azure.monitor.sync",
        "cartography.intel.azure.security_center.sync",
        "cartography.intel.azure.permission_relationships.sync",
    ]

    with ExitStack() as stack:
        for target in patches:
            stack.enter_context(patch(target))

        stack.enter_context(
            patch(
                "cartography.intel.azure.event_hub_namespace.sync_event_hub_namespaces",
                return_value=[],
            ),
        )
        stack.enter_context(
            patch(
                "cartography.intel.azure.data_factory.sync_data_factories",
                side_effect=AzureDataFactoryTransientError(
                    "list data factories",
                    503,
                ),
            ),
        )
        mock_linked_services = stack.enter_context(
            patch(
                "cartography.intel.azure.data_factory_linked_service.sync_data_factory_linked_services"
            ),
        )
        mock_datasets = stack.enter_context(
            patch(
                "cartography.intel.azure.data_factory_dataset.sync_data_factory_datasets"
            ),
        )
        mock_pipelines = stack.enter_context(
            patch(
                "cartography.intel.azure.data_factory_pipeline.sync_data_factory_pipelines"
            ),
        )
        mock_data_lake = stack.enter_context(
            patch("cartography.intel.azure.data_lake.sync"),
        )

        azure._sync_one_subscription(
            neo4j_session,
            credentials,
            "subscription-1",
            123,
            {"UPDATE_TAG": 123},
        )

        mock_linked_services.assert_not_called()
        mock_datasets.assert_not_called()
        mock_pipelines.assert_not_called()
        mock_data_lake.assert_called_once()


def test_get_factories_does_not_retry_non_transient_error() -> None:
    client = MagicMock()
    client.factories.list.side_effect = _SyntheticHttpResponseError(403)

    with (
        patch("cartography.intel.azure.data_factory_util.time.sleep") as mock_sleep,
        pytest.raises(HttpResponseError),
    ):
        data_factory.get_factories(client)

    assert client.factories.list.call_count == 1
    mock_sleep.assert_not_called()
