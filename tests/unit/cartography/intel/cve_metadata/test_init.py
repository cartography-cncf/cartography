from unittest.mock import call
from unittest.mock import MagicMock
from unittest.mock import patch

from cartography.config import Config
from cartography.graph.job import GraphJob
from cartography.intel import cve_metadata


def test_build_yearly_cve_batches_groups_by_feed_year():
    cve_ids = [
        "CVE-2024-0002",
        "CVE-1999-0001",
        "CVE-2024-0001",
        "CVE-2023-0001",
        "NOT-A-CVE",
    ]

    result = cve_metadata._build_yearly_cve_batches(cve_ids)

    assert result == [
        ["CVE-1999-0001"],
        ["CVE-2023-0001"],
        ["CVE-2024-0001", "CVE-2024-0002"],
    ]


@patch.object(cve_metadata, "merge_module_sync_metadata")
@patch.object(GraphJob, "from_node_schema")
@patch.object(cve_metadata, "load_cve_metadata_feed")
@patch.object(cve_metadata, "load_cve_metadata")
@patch.object(cve_metadata.epss, "merge_epss_into_cves")
@patch.object(cve_metadata.epss, "get_epss_scores")
@patch.object(cve_metadata.nvd, "merge_nvd_into_cves")
@patch.object(cve_metadata.nvd, "get_and_transform_nvd_cves")
@patch.object(cve_metadata, "get_cve_ids_from_graph")
@patch.object(cve_metadata, "Session")
def test_start_cve_metadata_ingestion_loads_one_year_at_a_time(
    mock_session_cls,
    mock_get_cve_ids_from_graph,
    mock_get_and_transform_nvd_cves,
    mock_merge_nvd_into_cves,
    mock_get_epss_scores,
    mock_merge_epss_into_cves,
    mock_load_cve_metadata,
    mock_load_cve_metadata_feed,
    mock_graphjob_from_node_schema,
    mock_merge_module_sync_metadata,
):
    mock_get_cve_ids_from_graph.return_value = [
        "CVE-2023-0002",
        "CVE-2024-0001",
        "CVE-2023-0001",
    ]
    http_session = MagicMock()
    mock_session_cls.return_value.__enter__.return_value = http_session
    mock_graphjob_from_node_schema.return_value.run = MagicMock()
    mock_get_and_transform_nvd_cves.side_effect = [
        {
            "CVE-2023-0001": {"id": "CVE-2023-0001", "baseScore": 1.0},
            "CVE-2023-0002": {"id": "CVE-2023-0002", "baseScore": 2.0},
        },
        {
            "CVE-2024-0001": {"id": "CVE-2024-0001", "baseScore": 3.0},
        },
    ]
    mock_get_epss_scores.side_effect = [
        {
            "CVE-2023-0001": {"epss_score": 0.1, "epss_percentile": 0.2},
            "CVE-2023-0002": {"epss_score": 0.3, "epss_percentile": 0.4},
        },
        {
            "CVE-2024-0001": {"epss_score": 0.5, "epss_percentile": 0.6},
        },
    ]
    config = Config(
        neo4j_uri="bolt://localhost:7687",
        update_tag=123,
    )
    neo4j_session = MagicMock()

    cve_metadata.start_cve_metadata_ingestion(neo4j_session, config)

    assert mock_get_and_transform_nvd_cves.call_args_list == [
        call(http_session, {"CVE-2023-0001", "CVE-2023-0002"}, api_key=None),
        call(http_session, {"CVE-2024-0001"}, api_key=None),
    ]
    assert mock_get_epss_scores.call_args_list == [
        call(http_session, ["CVE-2023-0001", "CVE-2023-0002"]),
        call(http_session, ["CVE-2024-0001"]),
    ]
    assert mock_load_cve_metadata_feed.call_args_list == [
        call(neo4j_session, 123, {"nvd", "epss"}),
    ]
    assert mock_load_cve_metadata.call_args_list == [
        call(
            neo4j_session,
            [{"id": "CVE-2023-0001"}, {"id": "CVE-2023-0002"}],
            123,
        ),
        call(
            neo4j_session,
            [{"id": "CVE-2024-0001"}],
            123,
        ),
    ]
    mock_merge_nvd_into_cves.assert_has_calls(
        [
            call(
                [{"id": "CVE-2023-0001"}, {"id": "CVE-2023-0002"}],
                {
                    "CVE-2023-0001": {"id": "CVE-2023-0001", "baseScore": 1.0},
                    "CVE-2023-0002": {"id": "CVE-2023-0002", "baseScore": 2.0},
                },
            ),
            call(
                [{"id": "CVE-2024-0001"}],
                {"CVE-2024-0001": {"id": "CVE-2024-0001", "baseScore": 3.0}},
            ),
        ],
    )
    mock_merge_epss_into_cves.assert_has_calls(
        [
            call(
                [{"id": "CVE-2023-0001"}, {"id": "CVE-2023-0002"}],
                {
                    "CVE-2023-0001": {"epss_score": 0.1, "epss_percentile": 0.2},
                    "CVE-2023-0002": {"epss_score": 0.3, "epss_percentile": 0.4},
                },
            ),
            call(
                [{"id": "CVE-2024-0001"}],
                {"CVE-2024-0001": {"epss_score": 0.5, "epss_percentile": 0.6}},
            ),
        ],
    )
    mock_graphjob_from_node_schema.assert_called_once()
    mock_merge_module_sync_metadata.assert_called_once()
