import copy
from datetime import datetime
from unittest.mock import MagicMock

from cartography.intel.cve_metadata import nvd
from cartography.intel.cve_metadata.nvd import merge_nvd_into_cves
from cartography.intel.cve_metadata.nvd import transform_cves
from tests.data.cve_metadata.nvd import GET_NVD_API_DATA


def _fresh_data():
    """Return a deep copy of test data so transform mutations don't leak between tests."""
    return copy.deepcopy(GET_NVD_API_DATA)


def test_transform_cves_filters_to_graph_cves():
    """Only CVEs present in the graph should be returned."""
    cve_ids_in_graph = {"CVE-2023-41782", "CVE-2024-22075"}
    result = transform_cves(_fresh_data(), cve_ids_in_graph)
    assert set(result.keys()) == {"CVE-2023-41782", "CVE-2024-22075"}
    assert "CVE-9999-0001" not in result


def test_transform_cves_extracts_descriptions():
    cve_ids_in_graph = {"CVE-2023-41782"}
    result = transform_cves(_fresh_data(), cve_ids_in_graph)
    cve = result["CVE-2023-41782"]
    assert (
        cve["description_en"]
        == "There is a DLL hijacking vulnerability in ZTE ZXCLOUD iRAI."
    )


def test_transform_cves_extracts_cvss():
    cve_ids_in_graph = {"CVE-2024-22075"}
    result = transform_cves(_fresh_data(), cve_ids_in_graph)
    cve = result["CVE-2024-22075"]
    assert cve["cvss_version"] == "3.1"
    assert cve["baseScore"] == 6.1
    assert cve["baseSeverity"] == "MEDIUM"
    assert cve["attackVector"] == "NETWORK"
    assert cve["exploitabilityScore"] == 2.8
    assert cve["impactScore"] == 2.7


def test_transform_cves_parses_dates():
    cve_ids_in_graph = {"CVE-2023-41782"}
    result = transform_cves(_fresh_data(), cve_ids_in_graph)
    cve = result["CVE-2023-41782"]
    assert cve["published"] == datetime.fromisoformat("2024-01-05T02:15:07.147")
    assert cve["lastModified"] == datetime.fromisoformat("2024-01-05T11:54:11.040")


def test_transform_cves_extracts_kev_fields():
    """CISA KEV fields should be passed through from NVD response."""
    cve_ids_in_graph = {"CVE-2024-22075"}
    result = transform_cves(_fresh_data(), cve_ids_in_graph)
    cve = result["CVE-2024-22075"]
    assert cve["cisaExploitAdd"] == "2024-01-08"
    assert cve["cisaActionDue"] == "2024-01-29"
    assert cve["cisaRequiredAction"] == "Apply mitigations per vendor instructions."
    assert cve["cisaVulnerabilityName"] == "Fireware HTML Injection Vulnerability"


def test_transform_cves_no_kev_fields():
    """CVEs without KEV data should not have those keys set."""
    cve_ids_in_graph = {"CVE-2023-41782"}
    result = transform_cves(_fresh_data(), cve_ids_in_graph)
    cve = result["CVE-2023-41782"]
    assert cve.get("cisaExploitAdd") is None
    assert cve.get("cisaActionDue") is None


def test_transform_cves_extracts_weaknesses():
    cve_ids_in_graph = {"CVE-2023-41782"}
    result = transform_cves(_fresh_data(), cve_ids_in_graph)
    cve = result["CVE-2023-41782"]
    assert cve["weaknesses"] == ["CWE-20"]


def test_transform_cves_extracts_references():
    cve_ids_in_graph = {"CVE-2023-41782"}
    result = transform_cves(_fresh_data(), cve_ids_in_graph)
    cve = result["CVE-2023-41782"]
    assert cve["references_urls"] == [
        "https://support.zte.com.cn/support/news/LoopholeInfoDetail.aspx?newsId=1032984",
    ]


def test_transform_cves_drops_raw_nvd_fields():
    data = _fresh_data()
    raw_cve = data["vulnerabilities"][0]["cve"]
    raw_cve["configurations"] = [{"nodes": [{"cpeMatch": ["unused"]}]}]

    result = transform_cves(data, {"CVE-2023-41782"})
    cve = result["CVE-2023-41782"]

    assert cve is not raw_cve
    assert "configurations" not in cve
    assert "metrics" not in cve
    assert "descriptions" not in cve
    assert "references" not in cve
    assert "sourceIdentifier" not in cve


def test_transform_cves_empty_graph():
    """When no CVE IDs are in the graph, result should be empty."""
    result = transform_cves(_fresh_data(), set())
    assert result == {}


def test_merge_nvd_into_cves():
    """NVD data should be merged into existing CVE dicts."""
    cves = [{"id": "CVE-2024-22075"}, {"id": "CVE-9999-0001"}]
    nvd_data = {
        "CVE-2024-22075": {
            "id": "CVE-2024-22075",
            "baseScore": 6.1,
            "baseSeverity": "MEDIUM",
        },
    }
    merge_nvd_into_cves(cves, nvd_data)
    assert cves[0]["baseScore"] == 6.1
    # CVE not in NVD should remain a stub
    assert "baseScore" not in cves[1]


def test_get_nvd_cves_from_feeds_deduplicates_2002_feed_year(monkeypatch):
    http_session = MagicMock()
    cve_ids_in_graph = {"CVE-1999-0001", "CVE-2002-0001"}

    captured_years = []

    def _fake_download(_http_session, year):
        captured_years.append(year)
        return {"vulnerabilities": []}

    monkeypatch.setattr(nvd, "_download_nvd_feed", _fake_download)

    result = nvd._get_nvd_cves_from_feeds(http_session, cve_ids_in_graph)
    assert result == {}
    assert captured_years == ["2002"]


def test_get_nvd_cves_from_feeds_maps_pre_2002_years_to_2002_feed(monkeypatch):
    http_session = MagicMock()
    cve_ids_in_graph = {"CVE-1999-0001"}

    captured_years = []

    def _fake_download(_http_session, year):
        captured_years.append(year)
        return {
            "vulnerabilities": [
                {
                    "cve": {
                        "id": "CVE-1999-0001",
                        "descriptions": [
                            {"lang": "en", "value": "old vulnerability"},
                        ],
                    },
                },
            ],
        }

    monkeypatch.setattr(nvd, "_download_nvd_feed", _fake_download)

    result = nvd._get_nvd_cves_from_feeds(http_session, cve_ids_in_graph)
    assert set(result) == {"CVE-1999-0001"}
    assert captured_years == ["2002"]
