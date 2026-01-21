from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.gcp.bigquery
import tests.data.gcp.bigquery
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_PROJECT_ID = "test-project"


def _create_test_project(neo4j_session):
    """Create a test GCP project node."""
    neo4j_session.run(
        """
        MERGE (project:GCPProject{id: $project_id})
        ON CREATE SET project.firstseen = timestamp()
        SET project.lastupdated = $update_tag
        """,
        project_id=TEST_PROJECT_ID,
        update_tag=TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.gcp.bigquery,
    "get_client",
    return_value=MagicMock(),
)
@patch.object(
    cartography.intel.gcp.bigquery,
    "get_datasets",
    return_value=tests.data.gcp.bigquery.DATASETS_RESPONSE,
)
@patch.object(
    cartography.intel.gcp.bigquery,
    "get_tables",
    return_value=tests.data.gcp.bigquery.TABLES_RESPONSE,
)
def test_sync_bigquery(mock_get_tables, mock_get_datasets, mock_get_client, neo4j_session):
    """
    Test that BigQuery sync correctly loads datasets and tables to Neo4j.
    """
    # Arrange - Create test project
    _create_test_project(neo4j_session)

    # Act
    cartography.intel.gcp.bigquery.sync(
        neo4j_session,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        None,  # credentials - will be mocked
        {"UPDATE_TAG": TEST_UPDATE_TAG, "PROJECT_ID": TEST_PROJECT_ID},
    )

    # Assert - Check datasets
    assert check_nodes(
        neo4j_session,
        "GCPBigQueryDataset",
        ["id", "dataset_id", "friendly_name"],
    ) == {
        (
            "test-project:test_dataset",
            "test_dataset",
            "Test Dataset",
        ),
    }

    # Assert - Check tables
    assert check_nodes(
        neo4j_session,
        "GCPBigQueryTable",
        ["id", "table_id", "type"],
    ) == {
        ("test-project:test_dataset.test_table", "test_table", "TABLE"),
        ("test-project:test_dataset.test_view", "test_view", "VIEW"),
    }

    # Assert - Check project to dataset relationship
    assert check_rels(
        neo4j_session,
        "GCPProject",
        "id",
        "GCPBigQueryDataset",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (TEST_PROJECT_ID, "test-project:test_dataset"),
    }

    # Assert - Check dataset to table relationship
    assert check_rels(
        neo4j_session,
        "GCPBigQueryDataset",
        "id",
        "GCPBigQueryTable",
        "id",
        "CONTAINS",
        rel_direction_right=True,
    ) == {
        ("test-project:test_dataset", "test-project:test_dataset.test_table"),
        ("test-project:test_dataset", "test-project:test_dataset.test_view"),
    }


def test_load_bigquery_datasets(neo4j_session):
    """
    Test that we can correctly transform and load BigQuery datasets to Neo4j.
    """
    # Arrange - Create test project
    _create_test_project(neo4j_session)

    # Transform and load datasets
    datasets_data = tests.data.gcp.bigquery.DATASETS_RESPONSE
    transformed_datasets = cartography.intel.gcp.bigquery.transform_datasets(datasets_data, TEST_PROJECT_ID)
    cartography.intel.gcp.bigquery.load_datasets(
        neo4j_session,
        transformed_datasets,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
    )

    # Assert - Check dataset properties
    query = """
    MATCH(dataset:GCPBigQueryDataset{id:$DatasetId})
    RETURN dataset.id, dataset.dataset_id, dataset.friendly_name, dataset.location
    """
    nodes = neo4j_session.run(
        query,
        DatasetId="test-project:test_dataset",
    )
    actual_nodes = {
        (n["dataset.id"], n["dataset.dataset_id"], n["dataset.friendly_name"], n["dataset.location"])
        for n in nodes
    }
    expected_nodes = {
        ("test-project:test_dataset", "test_dataset", "Test Dataset", "US"),
    }
    assert actual_nodes == expected_nodes


def test_load_bigquery_tables(neo4j_session):
    """
    Test that we can correctly transform and load BigQuery tables to Neo4j.
    """
    # Arrange - Create test project and dataset
    _create_test_project(neo4j_session)
    
    # Create dataset node
    neo4j_session.run(
        """
        MERGE (dataset:GCPBigQueryDataset{id: $dataset_id})
        ON CREATE SET dataset.firstseen = timestamp()
        SET dataset.lastupdated = $update_tag,
            dataset.dataset_id = $simple_dataset_id
        """,
        dataset_id="test-project:test_dataset",
        simple_dataset_id="test_dataset",
        update_tag=TEST_UPDATE_TAG,
    )

    # Transform and load tables
    tables_data = tests.data.gcp.bigquery.TABLES_RESPONSE
    transformed_tables = cartography.intel.gcp.bigquery.transform_tables(
        tables_data,
        TEST_PROJECT_ID,
        "test-project:test_dataset",
    )
    cartography.intel.gcp.bigquery.load_tables(
        neo4j_session,
        transformed_tables,
        TEST_UPDATE_TAG,
    )

    # Assert - Check table properties
    query = """
    MATCH(table:GCPBigQueryTable{id:$TableId})
    RETURN table.id, table.table_id, table.type
    """
    nodes = neo4j_session.run(
        query,
        TableId="test-project:test_dataset.test_table",
    )
    actual_nodes = {
        (n["table.id"], n["table.table_id"], n["table.type"])
        for n in nodes
    }
    expected_nodes = {
        ("test-project:test_dataset.test_table", "test_table", "TABLE"),
    }
    assert actual_nodes == expected_nodes
