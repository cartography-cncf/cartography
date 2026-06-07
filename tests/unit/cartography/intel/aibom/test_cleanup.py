from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from cartography.intel.aibom import sync_aibom_from_report_reader
from cartography.intel.common.object_store import ObjectStoreError
from cartography.intel.common.object_store import ReportRef
from tests.data.aibom.aibom_sample import AIBOM_REPORT


@patch("cartography.intel.aibom.cleanup_aibom")
@patch("cartography.intel.aibom.transform_aibom_component_payloads", return_value=[])
@patch(
    "cartography.intel.aibom.transform_aibom_source_payloads",
    return_value=[{"id": "source-1"}],
)
@patch("cartography.intel.aibom.load_aibom_sources")
@patch("cartography.intel.aibom.load_aibom_components")
@patch(
    "cartography.intel.aibom.prepare_aibom_report_for_ingestion",
    side_effect=[AIBOM_REPORT, ValueError("ambiguous anchoring")],
)
@patch(
    "cartography.intel.aibom.read_json_report",
    side_effect=[AIBOM_REPORT, AIBOM_REPORT],
)
@patch(
    "cartography.intel.aibom.filter_report_refs",
    return_value=[
        ReportRef(uri="/tmp/aibom-1.json", name="aibom-1.json"),
        ReportRef(uri="/tmp/aibom-2.json", name="aibom-2.json"),
    ],
)
def test_sync_aibom_from_report_reader_raises_on_preparation_failure_and_skips_cleanup(
    mock_filter_report_refs,
    mock_read_json_report,
    mock_prepare_report,
    mock_load_components,
    mock_load_sources,
    mock_transform_sources,
    mock_transform_components,
    mock_cleanup_aibom,
) -> None:
    neo4j_session = MagicMock()
    reader = MagicMock()
    reader.source_uri = "/tmp"
    reader.list_reports.return_value = []

    with pytest.raises(ValueError):
        sync_aibom_from_report_reader(
            neo4j_session,
            reader,
            123,
            {"UPDATE_TAG": 123},
        )

    mock_load_sources.assert_called_once()
    mock_cleanup_aibom.assert_not_called()


@patch("cartography.intel.aibom.cleanup_aibom")
@patch("cartography.intel.aibom.transform_aibom_component_payloads", return_value=[])
@patch(
    "cartography.intel.aibom.transform_aibom_source_payloads",
    return_value=[{"id": "source-1"}],
)
@patch("cartography.intel.aibom.load_aibom_sources")
@patch("cartography.intel.aibom.load_aibom_components")
@patch(
    "cartography.intel.aibom.prepare_aibom_report_for_ingestion",
    return_value=AIBOM_REPORT,
)
@patch(
    "cartography.intel.aibom.read_json_report",
    side_effect=ObjectStoreError("boom"),
)
@patch(
    "cartography.intel.aibom.filter_report_refs",
    return_value=[ReportRef(uri="/tmp/aibom-1.json", name="aibom-1.json")],
)
def test_sync_aibom_from_report_reader_skips_cleanup_on_read_failure(
    mock_filter_report_refs,
    mock_read_json_report,
    mock_prepare_report,
    mock_load_components,
    mock_load_sources,
    mock_transform_sources,
    mock_transform_components,
    mock_cleanup_aibom,
) -> None:
    neo4j_session = MagicMock()
    reader = MagicMock()
    reader.source_uri = "/tmp"
    reader.list_reports.return_value = []

    sync_aibom_from_report_reader(
        neo4j_session,
        reader,
        123,
        {"UPDATE_TAG": 123},
    )

    mock_load_sources.assert_not_called()
    mock_cleanup_aibom.assert_not_called()
