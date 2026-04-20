from unittest.mock import MagicMock
from unittest.mock import patch

from cartography.intel.gcp.bigquery_table import _enrich_bigquery_tables_with_details


def test_enrich_bigquery_tables_with_details_falls_back_to_sequential_without_credentials():
    shared_client = MagicMock(name="shared-bigquery-client")
    tables_raw = [
        {"tableReference": {"tableId": "users"}},
        {"tableReference": {"tableId": "events"}},
    ]
    seen_clients: list[object] = []

    def _mock_get_bigquery_table_detail(client, project_id, dataset_id, table_id):
        seen_clients.append(client)
        return {"tableReference": {"tableId": table_id}, "description": table_id}

    with (
        patch(
            "cartography.intel.gcp.bigquery_table.get_bigquery_table_detail",
            side_effect=_mock_get_bigquery_table_detail,
        ),
        patch(
            "cartography.intel.gcp.bigquery_table.build_bigquery_client"
        ) as mock_build_client,
    ):
        _enrich_bigquery_tables_with_details(
            shared_client,
            "test-project",
            "test_dataset",
            tables_raw,
            credentials=None,
            max_workers=4,
        )

    assert seen_clients == [shared_client, shared_client]
    assert [table["description"] for table in tables_raw] == ["users", "events"]
    mock_build_client.assert_not_called()


def test_enrich_bigquery_tables_with_details_uses_thread_local_clients_when_credentials_provided():
    shared_client = MagicMock(name="shared-bigquery-client")
    credentials = MagicMock()
    tables_raw = [
        {"tableReference": {"tableId": "users"}},
        {"tableReference": {"tableId": "events"}},
    ]
    seen_clients: list[object] = []

    def _mock_get_bigquery_table_detail(client, project_id, dataset_id, table_id):
        seen_clients.append(client)
        return {"tableReference": {"tableId": table_id}, "description": table_id}

    with (
        patch(
            "cartography.intel.gcp.bigquery_table.get_bigquery_table_detail",
            side_effect=_mock_get_bigquery_table_detail,
        ),
        patch(
            "cartography.intel.gcp.bigquery_table.build_bigquery_client",
            return_value=MagicMock(name="thread-bigquery-client"),
        ) as mock_build_client,
    ):
        _enrich_bigquery_tables_with_details(
            shared_client,
            "test-project",
            "test_dataset",
            tables_raw,
            credentials=credentials,
            max_workers=4,
        )

    assert seen_clients
    assert all(client is not shared_client for client in seen_clients)
    assert [table["description"] for table in tables_raw] == ["users", "events"]
    mock_build_client.assert_called()
