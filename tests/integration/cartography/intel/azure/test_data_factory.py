from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.azure.data_factory as data_factory
import cartography.intel.azure.data_factory_dataset as data_factory_dataset
import cartography.intel.azure.data_factory_linked_service as data_factory_linked_service
import cartography.intel.azure.data_factory_pipeline as data_factory_pipeline
from tests.data.azure.data_factory import MOCK_DATASETS
from tests.data.azure.data_factory import MOCK_FACTORIES
from tests.data.azure.data_factory import MOCK_LINKED_SERVICES
from tests.data.azure.data_factory import MOCK_PIPELINES
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_SUBSCRIPTION_ID = "00-00-00-00"
TEST_UPDATE_TAG = 123456789


@patch("cartography.intel.azure.data_factory_linked_service.get_linked_services")
@patch("cartography.intel.azure.data_factory_dataset.get_datasets")
@patch("cartography.intel.azure.data_factory_pipeline.get_pipelines")
@patch("cartography.intel.azure.data_factory.get_factories")
def test_sync_data_factory_internal_rels(
    mock_get_factories,
    mock_get_pipelines,
    mock_get_datasets,
    mock_get_ls,
    neo4j_session,
):
    """
    Test that we can correctly sync a Data Factory and its internal components and relationships.
    """
    # Arrange: Mock all four API calls
    mock_get_factories.return_value = MOCK_FACTORIES
    mock_get_pipelines.return_value = MOCK_PIPELINES
    mock_get_datasets.return_value = MOCK_DATASETS
    mock_get_ls.return_value = MOCK_LINKED_SERVICES

    # Create the prerequisite AzureSubscription node
    neo4j_session.run(
        "MERGE (s:AzureSubscription{id: $sub_id}) SET s.lastupdated = $tag",
        sub_id=TEST_SUBSCRIPTION_ID,
        tag=TEST_UPDATE_TAG,
    )

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "AZURE_SUBSCRIPTION_ID": TEST_SUBSCRIPTION_ID,
    }

    mock_client = MagicMock()

    # 1. Sync Factories
    factories_raw = data_factory.sync_data_factories(
        neo4j_session,
        mock_client,
        TEST_SUBSCRIPTION_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # 2. Sync Linked Services
    linked_services_by_factory = (
        data_factory_linked_service.sync_data_factory_linked_services(
            neo4j_session,
            mock_client,
            factories_raw,
            TEST_SUBSCRIPTION_ID,
            TEST_UPDATE_TAG,
            common_job_parameters,
        )
    )

    # 3. Sync Datasets
    datasets_by_factory = data_factory_dataset.sync_data_factory_datasets(
        neo4j_session,
        mock_client,
        factories_raw,
        linked_services_by_factory,
        TEST_SUBSCRIPTION_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # 4. Sync Pipelines
    data_factory_pipeline.sync_data_factory_pipelines(
        neo4j_session,
        mock_client,
        factories_raw,
        datasets_by_factory,
        TEST_SUBSCRIPTION_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert Nodes for all four types
    assert check_nodes(neo4j_session, "AzureDataFactory", ["id"]) == {
        (MOCK_FACTORIES[0]["id"],)
    }
    assert check_nodes(neo4j_session, "AzureDataFactoryPipeline", ["id"]) == {
        (MOCK_PIPELINES[0]["id"],)
    }
    assert check_nodes(neo4j_session, "AzureDataFactoryDataset", ["id"]) == {
        (MOCK_DATASETS[0]["id"],)
    }
    assert check_nodes(neo4j_session, "AzureDataFactoryLinkedService", ["id"]) == {
        (MOCK_LINKED_SERVICES[0]["id"],)
    }

    # Assert Relationships
    factory_id = MOCK_FACTORIES[0]["id"]
    pipeline_id = MOCK_PIPELINES[0]["id"]
    dataset_id = MOCK_DATASETS[0]["id"]
    ls_id = MOCK_LINKED_SERVICES[0]["id"]

    # Test :RESOURCE relationships to Subscription
    assert check_rels(
        neo4j_session, "AzureSubscription", "id", "AzureDataFactory", "id", "RESOURCE"
    ) == {(TEST_SUBSCRIPTION_ID, factory_id)}

    assert check_rels(
        neo4j_session,
        "AzureSubscription",
        "id",
        "AzureDataFactoryPipeline",
        "id",
        "RESOURCE",
    ) == {(TEST_SUBSCRIPTION_ID, pipeline_id)}

    assert check_rels(
        neo4j_session,
        "AzureSubscription",
        "id",
        "AzureDataFactoryDataset",
        "id",
        "RESOURCE",
    ) == {(TEST_SUBSCRIPTION_ID, dataset_id)}

    assert check_rels(
        neo4j_session,
        "AzureSubscription",
        "id",
        "AzureDataFactoryLinkedService",
        "id",
        "RESOURCE",
    ) == {(TEST_SUBSCRIPTION_ID, ls_id)}

    # Test :CONTAINS relationships to Factory
    assert check_rels(
        neo4j_session,
        "AzureDataFactory",
        "id",
        "AzureDataFactoryPipeline",
        "id",
        "CONTAINS",
    ) == {(factory_id, pipeline_id)}

    assert check_rels(
        neo4j_session,
        "AzureDataFactory",
        "id",
        "AzureDataFactoryDataset",
        "id",
        "CONTAINS",
    ) == {(factory_id, dataset_id)}

    assert check_rels(
        neo4j_session,
        "AzureDataFactory",
        "id",
        "AzureDataFactoryLinkedService",
        "id",
        "CONTAINS",
    ) == {(factory_id, ls_id)}

    # Test internal data flow relationships
    assert check_rels(
        neo4j_session,
        "AzureDataFactoryPipeline",
        "id",
        "AzureDataFactoryDataset",
        "id",
        "USES_DATASET",
    ) == {(pipeline_id, dataset_id)}

    assert check_rels(
        neo4j_session,
        "AzureDataFactoryDataset",
        "id",
        "AzureDataFactoryLinkedService",
        "id",
        "USES_LINKED_SERVICE",
    ) == {(dataset_id, ls_id)}


def test_sync_data_factory_linked_services_empty_factories(neo4j_session):
    """
    Test that syncing with an empty factories list doesn't crash with UnboundLocalError.
    Reproduces issue #2078.
    """
    # Create the prerequisite AzureSubscription node
    neo4j_session.run(
        "MERGE (s:AzureSubscription{id: $sub_id}) SET s.lastupdated = $tag",
        sub_id=TEST_SUBSCRIPTION_ID,
        tag=TEST_UPDATE_TAG,
    )

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "AZURE_SUBSCRIPTION_ID": TEST_SUBSCRIPTION_ID,
    }

    mock_client = MagicMock()

    # Call with empty factories list - this should trigger UnboundLocalError
    result = data_factory_linked_service.sync_data_factory_linked_services(
        neo4j_session,
        mock_client,
        [],  # Empty factories list
        TEST_SUBSCRIPTION_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Should return empty dict without crashing
    assert result == {}


def test_sync_data_factory_datasets_empty_factories(neo4j_session):
    """
    Test that syncing datasets with an empty factories list doesn't crash with UnboundLocalError.
    Reproduces issue #2078.
    """
    # Create the prerequisite AzureSubscription node
    neo4j_session.run(
        "MERGE (s:AzureSubscription{id: $sub_id}) SET s.lastupdated = $tag",
        sub_id=TEST_SUBSCRIPTION_ID,
        tag=TEST_UPDATE_TAG,
    )

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "AZURE_SUBSCRIPTION_ID": TEST_SUBSCRIPTION_ID,
    }

    mock_client = MagicMock()

    # Call with empty factories list - this should trigger UnboundLocalError
    result = data_factory_dataset.sync_data_factory_datasets(
        neo4j_session,
        mock_client,
        [],  # Empty factories list
        {},  # Empty linked_services dict
        TEST_SUBSCRIPTION_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Should return empty dict without crashing
    assert result == {}


def test_sync_data_factory_pipelines_empty_factories(neo4j_session):
    """
    Test that syncing pipelines with an empty factories list doesn't crash with UnboundLocalError.
    Reproduces issue #2078.
    """
    # Create the prerequisite AzureSubscription node
    neo4j_session.run(
        "MERGE (s:AzureSubscription{id: $sub_id}) SET s.lastupdated = $tag",
        sub_id=TEST_SUBSCRIPTION_ID,
        tag=TEST_UPDATE_TAG,
    )

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "AZURE_SUBSCRIPTION_ID": TEST_SUBSCRIPTION_ID,
    }

    mock_client = MagicMock()

    # Call with empty factories list - this should trigger UnboundLocalError
    data_factory_pipeline.sync_data_factory_pipelines(
        neo4j_session,
        mock_client,
        [],  # Empty factories list
        {},  # Empty datasets dict
        TEST_SUBSCRIPTION_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Should complete without crashing (no return value for this function)
