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

    with patch("time.sleep") as mock_sleep:
        result = data_factory.get_factories(client)

    assert result == [{"id": "factory-1"}]
    assert client.factories.list.call_count == 2
    mock_sleep.assert_called_once()


def test_sync_data_factories_skips_load_and_cleanup_on_transient_error() -> None:
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
        patch("time.sleep") as mock_sleep,
        pytest.raises(AzureDataFactoryTransientError) as excinfo,
    ):
        data_factory.get_factories(client)

    assert excinfo.value.operation == "list data factories"
    assert excinfo.value.status_code == 503
    assert isinstance(excinfo.value.__cause__, HttpResponseError)
    assert client.factories.list.call_count == 3
    assert mock_sleep.call_count == 2


def test_sync_data_factory_skips_child_syncs_after_transient_error() -> None:
    neo4j_session = MagicMock()
    credentials = MagicMock()

    with (
        patch(
            "cartography.intel.azure.data_factory.sync_data_factories",
            side_effect=AzureDataFactoryTransientError(
                "list data factories",
                503,
            ),
        ),
        patch(
            "cartography.intel.azure.data_factory_linked_service.sync_data_factory_linked_services"
        ) as mock_linked_services,
        patch(
            "cartography.intel.azure.data_factory_dataset.sync_data_factory_datasets"
        ) as mock_datasets,
        patch(
            "cartography.intel.azure.data_factory_pipeline.sync_data_factory_pipelines"
        ) as mock_pipelines,
    ):
        azure._sync_data_factory(
            neo4j_session,
            credentials,
            "subscription-1",
            123,
            {"UPDATE_TAG": 123},
        )

        mock_linked_services.assert_not_called()
        mock_datasets.assert_not_called()
        mock_pipelines.assert_not_called()


def test_sync_data_factory_skips_later_children_after_child_transient_error() -> None:
    neo4j_session = MagicMock()
    credentials = MagicMock()
    common_job_parameters = {"UPDATE_TAG": 123}
    factories = [{"id": "factory-1", "name": "factory-1"}]

    with (
        patch(
            "cartography.intel.azure.data_factory.sync_data_factories",
            return_value=factories,
        ) as mock_factories,
        patch(
            "cartography.intel.azure.data_factory_linked_service.sync_data_factory_linked_services",
            side_effect=AzureDataFactoryTransientError(
                "list data factory linked services",
                503,
            ),
        ) as mock_linked_services,
        patch(
            "cartography.intel.azure.data_factory_dataset.sync_data_factory_datasets"
        ) as mock_datasets,
        patch(
            "cartography.intel.azure.data_factory_pipeline.sync_data_factory_pipelines"
        ) as mock_pipelines,
    ):
        azure._sync_data_factory(
            neo4j_session,
            credentials,
            "subscription-1",
            123,
            common_job_parameters,
        )

    mock_factories.assert_called_once_with(
        neo4j_session,
        credentials,
        "subscription-1",
        123,
        common_job_parameters,
    )
    mock_linked_services.assert_called_once_with(
        neo4j_session,
        credentials,
        factories,
        "subscription-1",
        123,
        common_job_parameters,
    )
    mock_datasets.assert_not_called()
    mock_pipelines.assert_not_called()


def test_sync_data_factory_logs_subscription_when_skipping(
    caplog: pytest.LogCaptureFixture,
) -> None:
    neo4j_session = MagicMock()
    credentials = MagicMock()

    with patch(
        "cartography.intel.azure.data_factory.sync_data_factories",
        side_effect=AzureDataFactoryTransientError(
            "list data factories",
            503,
        ),
    ):
        azure._sync_data_factory(
            neo4j_session,
            credentials,
            "subscription-1",
            123,
            {"UPDATE_TAG": 123},
        )

    assert "subscription-1" in caplog.text


def test_sync_data_factory_runs_child_syncs_with_fetched_data() -> None:
    neo4j_session = MagicMock()
    credentials = MagicMock()
    common_job_parameters = {"UPDATE_TAG": 123}
    factories = [{"id": "factory-1", "name": "factory-1"}]
    linked_services = {"factory-1": [{"id": "linked-service-1"}]}
    datasets = {"factory-1": [{"id": "dataset-1"}]}

    with (
        patch(
            "cartography.intel.azure.data_factory.sync_data_factories",
            return_value=factories,
        ) as mock_factories,
        patch(
            "cartography.intel.azure.data_factory_linked_service.sync_data_factory_linked_services",
            return_value=linked_services,
        ) as mock_linked_services,
        patch(
            "cartography.intel.azure.data_factory_dataset.sync_data_factory_datasets",
            return_value=datasets,
        ) as mock_datasets,
        patch(
            "cartography.intel.azure.data_factory_pipeline.sync_data_factory_pipelines"
        ) as mock_pipelines,
    ):
        azure._sync_data_factory(
            neo4j_session,
            credentials,
            "subscription-1",
            123,
            common_job_parameters,
        )

    mock_factories.assert_called_once_with(
        neo4j_session,
        credentials,
        "subscription-1",
        123,
        common_job_parameters,
    )
    mock_linked_services.assert_called_once_with(
        neo4j_session,
        credentials,
        factories,
        "subscription-1",
        123,
        common_job_parameters,
    )
    mock_datasets.assert_called_once_with(
        neo4j_session,
        credentials,
        factories,
        linked_services,
        "subscription-1",
        123,
        common_job_parameters,
    )
    mock_pipelines.assert_called_once_with(
        neo4j_session,
        credentials,
        factories,
        datasets,
        "subscription-1",
        123,
        common_job_parameters,
    )


def test_get_factories_does_not_retry_non_transient_error() -> None:
    client = MagicMock()
    client.factories.list.side_effect = _SyntheticHttpResponseError(403)

    with (
        patch("time.sleep") as mock_sleep,
        pytest.raises(HttpResponseError),
    ):
        data_factory.get_factories(client)

    assert client.factories.list.call_count == 1
    mock_sleep.assert_not_called()


def test_get_factories_does_not_log_raw_error_body(
    caplog: pytest.LogCaptureFixture,
) -> None:
    client = MagicMock()
    client.factories.list.side_effect = [
        _SyntheticHttpResponseError(503),
        [_AzureResource({"id": "factory-1"})],
    ]

    with (
        patch("time.sleep"),
        patch.object(
            _SyntheticHttpResponseError, "__str__", return_value="raw-response-body"
        ),
    ):
        data_factory.get_factories(client)

    assert "raw-response-body" not in caplog.text
