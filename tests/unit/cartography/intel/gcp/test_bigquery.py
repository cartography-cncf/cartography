"""
Unit tests for GCP BigQuery intel module.
"""
from datetime import datetime
from unittest.mock import MagicMock, patch

from cartography.intel.gcp import bigquery


def test_get_client():
    """Test BigQuery client creation."""
    with patch('cartography.intel.gcp.bigquery.bigquery.Client') as mock_client:
        result = bigquery.get_client('test-project')
        mock_client.assert_called_once_with(project='test-project')
        assert result == mock_client.return_value


def test_get_datasets_success():
    """Test successful dataset retrieval with mocked BigQuery client."""
    mock_client = MagicMock()
    
    # Create a simple object with real attributes
    class MockDataset:
        dataset_id = 'test_dataset'
        location = 'US'
        friendly_name = 'Test Dataset'
        description = 'A test dataset'
        created = datetime(2025, 1, 1)
        modified = datetime(2025, 1, 15)
        labels = {}
    
    mock_dataset_list_item = MagicMock()
    mock_dataset_list_item.full_dataset_id = 'test-project:test_dataset'
    mock_dataset_list_item.reference = MagicMock()
    
    mock_client.list_datasets.return_value = [mock_dataset_list_item]
    mock_client.get_dataset.return_value = MockDataset()
    
    result = bigquery.get_datasets(mock_client, 'test-project')
    
    # Just verify we got a result with the right structure
    assert len(result) == 1
    assert 'id' in result[0]
    assert 'dataset_id' in result[0]
    assert 'project_id' in result[0]
    assert result[0]['project_id'] == 'test-project'


def test_get_datasets_empty():
    """Test dataset retrieval when no datasets exist."""
    mock_client = MagicMock()
    mock_client.list_datasets.return_value = []
    
    result = bigquery.get_datasets(mock_client, 'test-project')
    
    assert result == []


def test_get_datasets_exception():
    """Test dataset retrieval handles exceptions gracefully."""
    mock_client = MagicMock()
    mock_client.list_datasets.side_effect = Exception("API Error")
    
    result = bigquery.get_datasets(mock_client, 'test-project')
    
    assert result == []


def test_get_tables_success():
    """Test successful table retrieval."""
    mock_client = MagicMock()
    
    # Mock table
    mock_table = MagicMock()
    mock_table.table_id = 'test_table'
    mock_table.full_table_id = 'test-project:test_dataset.test_table'
    mock_table.friendly_name = 'Test Table'
    mock_table.description = 'A test table'
    mock_table.num_rows = 1000
    mock_table.num_bytes = 50000
    mock_table.table_type = 'TABLE'
    mock_table.created = '2025-01-01T00:00:00Z'
    mock_table.modified = '2025-01-15T00:00:00Z'
    
    mock_client.list_tables.return_value = [mock_table]
    
    result = bigquery.get_tables(mock_client, 'test_dataset', 'test-project')
    
    assert len(result) == 1
    assert result[0]['id'] == 'test-project.test_dataset.test_table'
    assert result[0]['table_id'] == 'test_table'
    assert result[0]['dataset_id'] == 'test_dataset'


def test_get_tables_empty():
    """Test table retrieval when no tables exist."""
    mock_client = MagicMock()
    mock_client.list_tables.return_value = []
    
    result = bigquery.get_tables(mock_client, 'test_dataset', 'test-project')
    
    assert result == []


def test_get_tables_exception():
    """Test table retrieval handles exceptions gracefully."""
    mock_client = MagicMock()
    mock_client.list_tables.side_effect = Exception("API Error")
    
    result = bigquery.get_tables(mock_client, 'test_dataset', 'test-project')
    
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


def test_cleanup():
    """Test cleanup of stale BigQuery data."""
    mock_session = MagicMock()
    common_job_parameters = {'UPDATE_TAG': 123456}
    
    bigquery.cleanup(mock_session, common_job_parameters)
    
    # Verify that cleanup queries were executed
    assert mock_session.run.called
