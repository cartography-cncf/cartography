from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.gcp.bigquery_connection as bigquery_connection
import cartography.intel.gcp.bigquery_dataset as bigquery_dataset
import cartography.intel.gcp.bigquery_routine as bigquery_routine
import cartography.intel.gcp.bigquery_table as bigquery_table
from tests.data.gcp.bigquery import MOCK_CONNECTIONS
from tests.data.gcp.bigquery import MOCK_DATASETS
from tests.data.gcp.bigquery import MOCK_ROUTINES_MY_DATASET
from tests.data.gcp.bigquery import MOCK_ROUTINES_OTHER_DATASET
from tests.data.gcp.bigquery import MOCK_TABLES_MY_DATASET
from tests.data.gcp.bigquery import MOCK_TABLES_OTHER_DATASET
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_PROJECT_ID = "test-project"


def _create_prerequisite_nodes(neo4j_session):
    neo4j_session.run(
        "MERGE (p:GCPProject {id: $project_id}) SET p.lastupdated = $tag",
        project_id=TEST_PROJECT_ID,
        tag=TEST_UPDATE_TAG,
    )


@patch("cartography.intel.gcp.bigquery_connection.get_bigquery_connections")
@patch("cartography.intel.gcp.bigquery_routine.get_bigquery_routines")
@patch("cartography.intel.gcp.bigquery_table.get_bigquery_tables")
@patch("cartography.intel.gcp.bigquery_dataset.get_bigquery_datasets")
def test_sync_bigquery(
    mock_get_datasets,
    mock_get_tables,
    mock_get_routines,
    mock_get_connections,
    neo4j_session,
):
    """
    Test the full BigQuery sync: datasets, tables, routines, and connections.
    """
    # Arrange
    mock_get_datasets.return_value = MOCK_DATASETS["datasets"]

    def _mock_get_tables(client, project_id, dataset_id):
        if dataset_id == "my_dataset":
            return MOCK_TABLES_MY_DATASET["tables"]
        elif dataset_id == "other_dataset":
            return MOCK_TABLES_OTHER_DATASET["tables"]
        return []

    mock_get_tables.side_effect = _mock_get_tables

    def _mock_get_routines(client, project_id, dataset_id):
        if dataset_id == "my_dataset":
            return MOCK_ROUTINES_MY_DATASET["routines"]
        elif dataset_id == "other_dataset":
            return MOCK_ROUTINES_OTHER_DATASET["routines"]
        return []

    mock_get_routines.side_effect = _mock_get_routines

    mock_get_connections.return_value = MOCK_CONNECTIONS["connections"]

    _create_prerequisite_nodes(neo4j_session)

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "PROJECT_ID": TEST_PROJECT_ID,
    }
    mock_client = MagicMock()

    # Act
    datasets_raw = bigquery_dataset.sync_bigquery_datasets(
        neo4j_session,
        mock_client,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    bigquery_table.sync_bigquery_tables(
        neo4j_session,
        mock_client,
        datasets_raw,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    bigquery_routine.sync_bigquery_routines(
        neo4j_session,
        mock_client,
        datasets_raw,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    bigquery_connection.sync_bigquery_connections(
        neo4j_session,
        mock_client,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert datasets
    assert check_nodes(
        neo4j_session,
        "GCPBigQueryDataset",
        ["id", "dataset_id", "location"],
    ) == {
        ("test-project:my_dataset", "my_dataset", "US"),
        ("test-project:other_dataset", "other_dataset", "EU"),
    }

    # Assert datasets also have the Database ontology label
    result = neo4j_session.run(
        "MATCH (n:Database:GCPBigQueryDataset) RETURN count(n) AS cnt",
    )
    assert result.single()["cnt"] == 2

    # Assert tables
    assert check_nodes(
        neo4j_session,
        "GCPBigQueryTable",
        ["id", "table_id", "type"],
    ) == {
        ("test-project:my_dataset.users", "users", "TABLE"),
        ("test-project:my_dataset.user_view", "user_view", "VIEW"),
        ("test-project:other_dataset.events", "events", "TABLE"),
    }

    # Assert routines
    assert check_nodes(
        neo4j_session,
        "GCPBigQueryRoutine",
        ["id", "routine_id", "routine_type"],
    ) == {
        ("test-project:my_dataset.my_udf", "my_udf", "SCALAR_FUNCTION"),
    }

    # Assert connections
    assert check_nodes(
        neo4j_session,
        "GCPBigQueryConnection",
        ["id", "friendly_name", "connection_type"],
    ) == {
        (
            "projects/test-project/locations/us/connections/my-cloud-sql-conn",
            "My Cloud SQL Connection",
            "cloudSql",
        ),
        (
            "projects/test-project/locations/us/connections/my-spark-conn",
            "My Spark Connection",
            "spark",
        ),
    }

    # Assert project -> dataset relationships
    assert check_rels(
        neo4j_session,
        "GCPProject",
        "id",
        "GCPBigQueryDataset",
        "id",
        "RESOURCE",
    ) == {
        (TEST_PROJECT_ID, "test-project:my_dataset"),
        (TEST_PROJECT_ID, "test-project:other_dataset"),
    }

    # Assert project -> table relationships
    assert check_rels(
        neo4j_session,
        "GCPProject",
        "id",
        "GCPBigQueryTable",
        "id",
        "RESOURCE",
    ) == {
        (TEST_PROJECT_ID, "test-project:my_dataset.users"),
        (TEST_PROJECT_ID, "test-project:my_dataset.user_view"),
        (TEST_PROJECT_ID, "test-project:other_dataset.events"),
    }

    # Assert dataset -> table relationships
    assert check_rels(
        neo4j_session,
        "GCPBigQueryDataset",
        "id",
        "GCPBigQueryTable",
        "id",
        "HAS_TABLE",
    ) == {
        ("test-project:my_dataset", "test-project:my_dataset.users"),
        ("test-project:my_dataset", "test-project:my_dataset.user_view"),
        ("test-project:other_dataset", "test-project:other_dataset.events"),
    }

    # Assert project -> routine relationships
    assert check_rels(
        neo4j_session,
        "GCPProject",
        "id",
        "GCPBigQueryRoutine",
        "id",
        "RESOURCE",
    ) == {
        (TEST_PROJECT_ID, "test-project:my_dataset.my_udf"),
    }

    # Assert dataset -> routine relationships
    assert check_rels(
        neo4j_session,
        "GCPBigQueryDataset",
        "id",
        "GCPBigQueryRoutine",
        "id",
        "HAS_ROUTINE",
    ) == {
        ("test-project:my_dataset", "test-project:my_dataset.my_udf"),
    }

    # Assert project -> connection relationships
    assert check_rels(
        neo4j_session,
        "GCPProject",
        "id",
        "GCPBigQueryConnection",
        "id",
        "RESOURCE",
    ) == {
        (
            TEST_PROJECT_ID,
            "projects/test-project/locations/us/connections/my-cloud-sql-conn",
        ),
        (
            TEST_PROJECT_ID,
            "projects/test-project/locations/us/connections/my-spark-conn",
        ),
    }
