"""  
Unit tests for GCP BigQuery intel module.
"""
from datetime import datetime
from unittest.mock import MagicMock, patch

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
    
    mock_dataset_list_item = MagicMock()
    mock_dataset_list_item.reference = MagicMock()
    
    mock_client.list_datasets.return_value = [mock_dataset_list_item]
    mock_client.get_dataset.return_value = MockDataset()
    
    # Test get function
    raw_datasets = bigquery.get_datasets(mock_client)
    assert len(raw_datasets) == 1
    assert raw_datasets[0].dataset_id == 'test_dataset'
    
    # Test transform function
    transformed = bigquery.transform_datasets(raw_datasets, 'test-project')
    assert len(transformed) == 1
    assert 'id' in transformed[0]
    assert 'dataset_id' in transformed[0]
    assert 'project_id' in transformed[0]
    assert transformed[0]['project_id'] == 'test-project'


def test_get_datasets_empty():
    """Test dataset retrieval when no datasets exist."""
    mock_client = MagicMock()
    mock_client.list_datasets.return_value = []
    
    result = bigquery.get_datasets(mock_client)
    
    assert result == []


def test_get_tables_success():
    """Test successful table retrieval."""
    mock_client = MagicMock()
    
    # Mock table
    mock_table = MagicMock()
    mock_table.table_id = 'test_table'
    mock_table.table_type = 'TABLE'
    mock_table.created = datetime(2025, 1, 1)
    mock_table.expires = None
    
    mock_client.list_tables.return_value = [mock_table]
    
    # Test get function
    raw_tables = bigquery.get_tables(mock_client, 'test_dataset')
    assert len(raw_tables) == 1
    assert raw_tables[0].table_id == 'test_table'
    
    # Test transform function
    transformed = bigquery.transform_tables(raw_tables, 'test_dataset', 'test-project')
    assert len(transformed) == 1
    assert transformed[0]['id'] == 'test-project.test_dataset.test_table'
    assert transformed[0]['table_id'] == 'test_table'
    assert transformed[0]['dataset_id'] == 'test_dataset'


def test_get_tables_empty():
    """Test table retrieval when no tables exist."""
    mock_client = MagicMock()
    mock_client.list_tables.return_value = []
    
    result = bigquery.get_tables(mock_client, 'test_dataset')
    
    assert result == []


def test_load_datasets():
    """Test dataset loading into Neo4j."""
    mock_session = MagicMock()
    datasets = [
        {
            'id': 'test-project.dataset1',
            'dataset_id': 'dataset1',
            'project_id': 'test-project',
            'location': 'US',
            'friendly_name': 'Dataset 1',
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
            'dataset_id': 'dataset1',
            'project_id': 'test-project',
            'num_rows': 1000,
        },
    ]
    
    bigquery.load_tables(mock_session, tables, 'dataset1', 'test-project', 123456)
    
    # Verify that Neo4j session run was called
    assert mock_session.run.called


@patch('cartography.intel.gcp.bigquery.run_cleanup_job')
def test_cleanup_bigquery(mock_cleanup):
    """Test cleanup of stale BigQuery data."""
    mock_session = MagicMock()
    common_job_parameters = {'UPDATE_TAG': 123456}
    
    bigquery.cleanup_bigquery(mock_session, common_job_parameters)
    
    # Verify that run_cleanup_job was called with the right parameters
    mock_cleanup.assert_called_once_with(
        'gcp_bigquery_cleanup.json',
        mock_session,
        common_job_parameters,
    )
