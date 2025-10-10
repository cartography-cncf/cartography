from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.azure.data_factory as data_factory
from tests.data.azure.data_factory import MOCK_DATASETS
from tests.data.azure.data_factory import MOCK_FACTORIES
from tests.data.azure.data_factory import MOCK_LINKED_SERVICES
from tests.data.azure.data_factory import MOCK_PIPELINES
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_SUBSCRIPTION_ID = "00-00-00-00"
TEST_UPDATE_TAG = 123456789


@patch("cartography.intel.azure.data_factory.get_linked_services")
@patch("cartography.intel.azure.data_factory.get_datasets")
@patch("cartography.intel.azure.data_factory.get_pipelines")
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

    # Act
    data_factory.sync(
        neo4j_session,
        MagicMock(),
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

    # Test :RESOURCE and :CONTAINS relationships
    expected_hierarchy = {
        (TEST_SUBSCRIPTION_ID, factory_id),
        (factory_id, pipeline_id),
        (factory_id, dataset_id),
        (factory_id, ls_id),
    }
    actual_hierarchy = check_rels(
        neo4j_session,
        "AzureSubscription",
        "id",
        "AzureDataFactory",
        "id",
        "RESOURCE",
    )
    actual_hierarchy.update(
        check_rels(
            neo4j_session,
            "AzureDataFactory",
            "id",
            "AzureDataFactoryPipeline",
            "id",
            "CONTAINS",
        ),
    )
    actual_hierarchy.update(
        check_rels(
            neo4j_session,
            "AzureDataFactory",
            "id",
            "AzureDataFactoryDataset",
            "id",
            "CONTAINS",
        ),
    )
    actual_hierarchy.update(
        check_rels(
            neo4j_session,
            "AzureDataFactory",
            "id",
            "AzureDataFactoryLinkedService",
            "id",
            "CONTAINS",
        ),
    )
    assert actual_hierarchy == expected_hierarchy

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
