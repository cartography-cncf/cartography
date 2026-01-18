"""
Unit tests for GCP BigQuery intel module.
"""
from datetime import datetime
from unittest.mock import MagicMock
from unittest.mock import patch

from cartography.intel.gcp import bigquery


def test_get_datasets_success():
    """Test successful dataset retrieval with mocked BigQuery client."""
    mock_client = MagicMock()

    # Create a simple object with real attributes
    class MockDataset:
        dataset_id = 'test_dataset'
        location = 'US'
        friendly_name = 'Test Dataset'
        full_dataset_id = 'test-project:test_dataset'
        description = 'A test dataset'
        created = datetime(2025, 1, 1)
        modified = datetime(2025, 1, 15)

    class MockDatasetListItem:
        reference = MagicMock()
        full_dataset_id = 'test-project:test_dataset'

    mock_client.list_datasets.return_value = [MockDatasetListItem()]
    mock_client.get_dataset.return_value = MockDataset()

    # Test get function (now returns transformed data directly)
    datasets = bigquery.get_datasets(mock_client, 'test-project')
    assert len(datasets) == 1
    assert datasets[0]['dataset_id'] == 'test_dataset'
    assert datasets[0]['project_id'] == 'test-project'
    assert datasets[0]['location'] == 'US'
    assert datasets[0]['id'] == 'test-project.test_dataset'


def test_get_datasets_empty():
    """Test dataset retrieval when no datasets exist."""
    mock_client = MagicMock()
    mock_client.list_datasets.return_value = []

    result = bigquery.get_datasets(mock_client, 'test-project')

    assert result == []


def test_get_tables_success():
    """Test successful table retrieval."""
    mock_client = MagicMock()

    # Mock table
    class MockTable:
        table_id = 'test_table'
        table_type = 'TABLE'
        created = datetime(2025, 1, 1)
        expires = None

    mock_client.list_tables.return_value = [MockTable()]
    mock_client.dataset.return_value = MagicMock()

    # Test get function (now returns transformed data directly)
    tables = bigquery.get_tables(mock_client, 'test_dataset', 'test-project')
    assert len(tables) == 1
    assert tables[0]['table_id'] == 'test_table'
    assert tables[0]['id'] == 'test-project.test_dataset.test_table'
    assert tables[0]['type'] == 'TABLE'


def test_get_tables_empty():
    """Test table retrieval when no tables exist."""
    mock_client = MagicMock()
    mock_client.list_tables.return_value = []
    mock_client.dataset.return_value = MagicMock()

    result = bigquery.get_tables(mock_client, 'test_dataset', 'test-project')

    assert result == []


def test_load_datasets():
    """Test dataset loading into Neo4j."""
    mock_session = MagicMock()
    datasets = [
        {
            'id': 'test-project.dataset1',
            'dataset_id': 'dataset1',
            'location': 'US',
            'friendly_name': 'Dataset 1',
            'full_dataset_id': 'test-project:dataset1',
            'description': 'Test',
            'created': '2025-01-01',
            'modified': '2025-01-15',
        },
    ]

    bigquery.load_datasets(mock_session, datasets, 'test-project', 123456)

    # Verify that Neo4j session run was called
    assert mock_session.run.called


def test_load_tables():
    """Test table loading into Neo4j."""
    mock_session = MagicMock()
    tables = [
        {
            'id': 'test-project.dataset1.table1',
            'table_id': 'table1',
            'dataset_id': 'test-project.dataset1',
            'project_id': 'test-project',
            'type': 'TABLE',
            'creation_time': '2025-01-01',
            'expires': None,
        },
    ]

    bigquery.load_tables(mock_session, tables, 'test-project.dataset1', 123456)

    # Verify that Neo4j session run was called
    assert mock_session.run.called


@patch('cartography.intel.gcp.bigquery.GraphJob')
def test_cleanup_datasets(mock_graph_job):
    """Test cleanup of stale BigQuery datasets."""
    mock_session = MagicMock()
    common_job_parameters = {'UPDATE_TAG': 123456, 'PROJECT_ID': 'test-project'}

    # Mock the GraphJob chain
    mock_job_instance = MagicMock()
    mock_graph_job.from_node_schema.return_value = mock_job_instance

    # Should not raise an error
    bigquery.cleanup_datasets(mock_session, common_job_parameters)

    # Verify GraphJob was called correctly
    mock_graph_job.from_node_schema.assert_called_once()
    mock_job_instance.run.assert_called_once_with(mock_session)
