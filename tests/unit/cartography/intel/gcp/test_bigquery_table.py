from unittest.mock import MagicMock
from unittest.mock import patch

from cartography.intel.gcp.bigquery_table import _enrich_bigquery_tables_with_details


def test_enrich_bigquery_tables_with_details_uses_bounded_concurrency():
    tables_raw = [
        {"tableReference": {"tableId": "users"}},
        {"tableReference": {"tableId": "events"}},
        {"tableReference": {"tableId": "views"}},
    ]
    detail_map = {
        "users": {"numRows": "100", "description": "Users"},
        "events": None,
        "views": {"numRows": "200", "description": "Views"},
    }

    with (
        patch(
            "cartography.intel.gcp.bigquery_table.build_client",
            return_value=MagicMock(),
        ) as mock_build_client,
        patch(
            "cartography.intel.gcp.bigquery_table.get_bigquery_table_detail",
            side_effect=lambda client, project_id, dataset_id, table_id: detail_map[
                table_id
            ],
        ) as mock_get_detail,
    ):
        _enrich_bigquery_tables_with_details(
            client=MagicMock(),
            project_id="test-project",
            dataset_id="analytics",
            tables_raw=tables_raw,
            credentials=MagicMock(),
            max_workers=2,
        )

    assert tables_raw == [
        {
            "tableReference": {"tableId": "users"},
            "numRows": "100",
            "description": "Users",
        },
        {"tableReference": {"tableId": "events"}},
        {
            "tableReference": {"tableId": "views"},
            "numRows": "200",
            "description": "Views",
        },
    ]
    assert mock_get_detail.call_count == 3
    assert 1 <= mock_build_client.call_count <= 2
