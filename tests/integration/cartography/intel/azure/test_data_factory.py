from unittest.mock import MagicMock, patch

import cartography.intel.azure.data_factory as data_factory
from tests.data.azure.data_factory import MOCK_DATASETS, MOCK_FACTORIES, MOCK_LINKED_SERVICES, MOCK_PIPELINES
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_SUBSCRIPTION_ID = "00-00-00-00"
TEST_UPDATE_TAG = 123456789


@patch("cartography.intel.azure.data_factory.get_linked_services")
@patch("cartography.intel.azure.data_factory.get_datasets")
@patch("cartography.intel.azure.data_factory.get_pipelines")
@patch("cartography.intel.azure.data_factory.get_factories")
def test_sync_data_factory(mock_get_factories, mock_get_pipelines, mock_get_datasets, mock_get_ls, neo4j_session):
    """
    Test that we can correctly sync Data Factory and its child components.
    """
    # Arrange
    mock_get_factories.return_value = MOCK_FACTORIES
    mock_get_pipelines.return_value = MOCK_PIPELINES
    mock_get_datasets.return_value = MOCK_DATASETS
    mock_get_ls.return_value = MOCK_LINKED_SERVICES

    # Create the prerequisite AzureSubscription node
    neo4j_session.run(
        """
        MERGE (s:AzureSubscription{id: $sub_id})
        SET s.lastupdated = $update_tag
        """,
        sub_id=TEST_SUBSCRIPTION_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "AZURE_SUBSCRIPTION_ID": TEST_SUBSCRIPTION_ID,
    }

    # Act
    data_factory.sync(
        neo4j_session,
        MagicMock(),
        TEST_SUBSCRIPTION_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert Factories
    expected_factories = {(MOCK_FACTORIES[0]['id'], MOCK_FACTORIES[0]['name'])}
    actual_factories = check_nodes(neo4j_session, "AzureDataFactory", ["id", "name"])
    assert actual_factories == expected_factories

    # Assert Pipelines
    expected_pipelines = {(MOCK_PIPELINES[0]['id'], MOCK_PIPELINES[0]['name'])}
    actual_pipelines = check_nodes(neo4j_session, "AzureDataFactoryPipeline", ["id", "name"])
    assert actual_pipelines == expected_pipelines

    # Assert Datasets
    expected_datasets = {(MOCK_DATASETS[0]['id'], MOCK_DATASETS[0]['name'])}
    actual_datasets = check_nodes(neo4j_session, "AzureDataFactoryDataset", ["id", "name"])
    assert actual_datasets == expected_datasets

    # Assert Linked Services
    expected_ls = {(MOCK_LINKED_SERVICES[0]['id'], MOCK_LINKED_SERVICES[0]['name'])}
    actual_ls = check_nodes(neo4j_session, "AzureDataFactoryLinkedService", ["id", "name"])
    assert actual_ls == expected_ls

    # Assert Relationships
    factory_id = MOCK_FACTORIES[0]['id']
    pipeline_id = MOCK_PIPELINES[0]['id']
    dataset_id = MOCK_DATASETS[0]['id']
    ls_id = MOCK_LINKED_SERVICES[0]['id']

    expected_rels = {
        (TEST_SUBSCRIPTION_ID, factory_id),
        (factory_id, pipeline_id),
        (factory_id, dataset_id),
        (factory_id, ls_id),
    }
    actual_rels = check_rels(
        neo4j_session, "AzureSubscription", "id", "AzureDataFactory", "id", "RESOURCE",
    )
    actual_rels.update(
        check_rels(
            neo4j_session, "AzureDataFactory", "id", "AzureDataFactoryPipeline", "id", "CONTAINS",
        ),
    )
    actual_rels.update(
        check_rels(
            neo4j_session, "AzureDataFactory", "id", "AzureDataFactoryDataset", "id", "CONTAINS",
        ),
    )
    actual_rels.update(
        check_rels(
            neo4j_session, "AzureDataFactory", "id", "AzureDataFactoryLinkedService", "id", "CONTAINS",
        ),
    )
    assert actual_rels == expected_rels