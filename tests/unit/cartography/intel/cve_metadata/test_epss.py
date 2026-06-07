from unittest.mock import MagicMock

from cartography.intel.cve_metadata.epss import get_epss_scores
from cartography.intel.cve_metadata.epss import merge_epss_into_cves
from tests.data.cve_metadata.epss import GET_EPSS_API_DATA


def test_get_epss_scores():
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.json.return_value = GET_EPSS_API_DATA
    mock_session.get.return_value = mock_response

    result = get_epss_scores(mock_session, ["CVE-2023-41782", "CVE-2024-22075"])

    assert "CVE-2023-41782" in result
    assert result["CVE-2023-41782"]["epss_score"] == 0.00043
    assert result["CVE-2023-41782"]["epss_percentile"] == 0.08931
    assert result["CVE-2024-22075"]["epss_score"] == 0.97530
    assert result["CVE-2024-22075"]["epss_percentile"] == 0.99940


def test_get_epss_scores_batching():
    """Test that large lists of CVEs are batched into multiple requests."""
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.json.return_value = {"data": []}
    mock_session.get.return_value = mock_response

    # 250 CVEs should require 3 batches (100 + 100 + 50)
    cve_ids = [f"CVE-2024-{i:04d}" for i in range(250)]
    get_epss_scores(mock_session, cve_ids)

    assert mock_session.get.call_count == 3


def test_merge_epss_into_cves():
    cves = [
        {"id": "CVE-2023-41782"},
        {"id": "CVE-2024-22075"},
        {"id": "CVE-9999-0001"},
    ]
    epss_data = {
        "CVE-2023-41782": {"epss_score": 0.00043, "epss_percentile": 0.08931},
        "CVE-2024-22075": {"epss_score": 0.97530, "epss_percentile": 0.99940},
    }

    merge_epss_into_cves(cves, epss_data)

    assert cves[0]["epss_score"] == 0.00043
    assert cves[0]["epss_percentile"] == 0.08931
    assert cves[1]["epss_score"] == 0.97530
    # CVE not in EPSS data should have None
    assert cves[2]["epss_score"] is None
    assert cves[2]["epss_percentile"] is None
