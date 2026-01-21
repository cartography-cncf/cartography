# flake8: noqa
from datetime import datetime
from unittest.mock import MagicMock


def create_test_dataset():
    """Create a mock BigQuery dataset for testing."""
    dataset = MagicMock()
    dataset.full_dataset_id = "test-project:test_dataset"
    dataset.dataset_id = "test_dataset"
    dataset.project = "test-project"
    dataset.friendly_name = "Test Dataset"
    dataset.description = "A test dataset for integration tests"
    dataset.location = "US"
    dataset.created = datetime(2021, 12, 20, 10, 0, 0)
    dataset.modified = datetime(2021, 12, 21, 12, 0, 0)
    return dataset


def create_test_table():
    """Create a mock BigQuery table for testing."""
    table = MagicMock()
    table.table_id = "test_table"
    table.dataset_id = "test_dataset"
    table.project = "test-project"
    table.table_type = "TABLE"
    table.created = datetime(2021, 12, 20, 10, 0, 0)
    table.expires = None
    return table


def create_test_view():
    """Create a mock BigQuery view for testing."""
    view = MagicMock()
    view.table_id = "test_view"
    view.dataset_id = "test_dataset"
    view.project = "test-project"
    view.table_type = "VIEW"
    view.created = datetime(2021, 12, 20, 12, 30, 0)
    view.expires = None
    return view


# Mock responses
DATASETS_RESPONSE = [create_test_dataset()]

TABLES_RESPONSE = [
    create_test_table(),
    create_test_view(),
]
