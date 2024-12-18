from datetime import datetime
from datetime import timedelta
from datetime import timezone
from unittest.mock import MagicMock
from unittest.mock import Mock
from unittest.mock import patch

import pytest
from requests import Session

from cartography.intel.cve.feed import _call_cves_api
from cartography.intel.cve.feed import _map_cve_dict
from cartography.intel.cve.feed import get_cves_in_batches
from cartography.intel.cve.feed import get_modified_cves
from cartography.intel.cve.feed import get_published_cves_per_year
from tests.data.cve.feed import GET_CVE_API_DATA
from tests.data.cve.feed import GET_CVE_API_DATA_BATCH_2

NIST_CVE_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0/"
API_KEY = "nvd_api_key"


@pytest.fixture
def mock_session():
    return MagicMock(spec=Session)


@pytest.fixture(autouse=True)
def mock_time_sleep(mocker):
    return mocker.patch("time.sleep")


def _mock_good_responses() -> list[Mock]:
    mock_response_1 = Mock()
    mock_response_1.status_code = 200
    mock_response_1.json.return_value = {
        "resultsPerPage": 2000,
        "startIndex": 0,
        "totalResults": 4000,
        "format": "NVD_CVE",
        "version": "2.0",
        "timestamp": "2024-01-10T19:30:07.520",
        "vulnerabilities": [
            {
                "cve": {
                    "id": "CVE-2024-001",
                },
            },
            {
                "cve": {
                    "id": "CVE-2024-002",
                },
            },
            {
                "cve": {
                    "id": "CVE-2024-003",
                },
            },
        ],
    }
    mock_response_2 = Mock()
    mock_response_2.status_code = 200
    mock_response_2.json.return_value = {
        "resultsPerPage": 2000,
        "startIndex": 2000,
        "totalResults": 4000,
        "format": "NVD_CVE",
        "version": "2.0",
        "timestamp": "2024-01-10T19:30:07.520",
        "vulnerabilities": [
            {
                "cve": {
                    "id": "CVE-2024-004",
                },
            },
            {
                "cve": {
                    "id": "CVE-2024-005",
                },
            },
            {
                "cve": {
                    "id": "CVE-2024-006",
                },
            },
        ],
    }
    mock_response_3 = Mock()
    mock_response_3.status_code = 200
    mock_response_3.json.return_value = {
        "resultsPerPage": 0,
        "startIndex": 4000,
        "totalResults": 4000,
        "format": "NVD_CVE",
        "version": "2.0",
        "timestamp": "2024-01-10T19:30:07.520",
        "vulnerabilities": [],
    }
    return [mock_response_1, mock_response_2, mock_response_3]


def test_call_cves_api(mock_session):
    # Arrange
    mock_session.get.side_effect = _mock_good_responses()
    params = {"start": "2024-01-10T00:00:00Z", "end": "2024-01-10T23:59:59Z"}
    expected_result = {
        "resultsPerPage": 0,
        "startIndex": 4000,
        "totalResults": 4000,
        "format": "NVD_CVE",
        "version": "2.0",
        "timestamp": "2024-01-10T19:30:07.520",
        "vulnerabilities": [
            {
                "cve": {
                    "id": "CVE-2024-001",
                },
            },
            {
                "cve": {
                    "id": "CVE-2024-002",
                },
            },
            {
                "cve": {
                    "id": "CVE-2024-003",
                },
            },
            {
                "cve": {
                    "id": "CVE-2024-004",
                },
            },
            {
                "cve": {
                    "id": "CVE-2024-005",
                },
            },
            {
                "cve": {
                    "id": "CVE-2024-006",
                },
            },
        ],
    }

    # Act
    result = _call_cves_api(mock_session, NIST_CVE_URL, API_KEY, params)

    # Assert
    assert mock_session.get.call_count == 3
    assert result == expected_result


@patch("cartography.intel.cve.feed._call_cves_api")
def test_get_cves_in_batches(mock_call_cves_api: Mock, mock_session: Session):
    """
    Ensure that we get the correct number of CVEs in batches of 120 days
    """
    # Arrange
    mock_call_cves_api.side_effect = [
        GET_CVE_API_DATA,
        GET_CVE_API_DATA_BATCH_2,
    ]
    start_date = datetime.strptime("2024-01-01T00:00:00Z", "%Y-%m-%dT%H:%M:%SZ")
    end_date = datetime.strptime("2024-05-01T00:00:00Z", "%Y-%m-%dT%H:%M:%SZ")
    date_param_names = {
        "start": "startDate",
        "end": "endDate",
    }
    excepted_cves = GET_CVE_API_DATA.copy()
    _map_cve_dict(excepted_cves, GET_CVE_API_DATA_BATCH_2)
    # Act
    cves = get_cves_in_batches(
        mock_session, NIST_CVE_URL, start_date, end_date, date_param_names, API_KEY,
    )
    # Assert
    assert mock_call_cves_api.call_count == 2
    assert cves == excepted_cves


@patch("cartography.intel.cve.feed._call_cves_api")
def test_get_modified_cves(mock_call_cves_api: Mock, mock_session: Session):
    # Arrange
    mock_call_cves_api.side_effect = [GET_CVE_API_DATA]
    last_modified_date = datetime.now(tz=timezone.utc) + timedelta(days=-1)
    last_modified_date_iso8601 = last_modified_date.strftime("%Y-%m-%dT%H:%M:%S")
    current_date_iso8601 = datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    expected_params = {
        "lastModStartDate": last_modified_date_iso8601,
        "lastModEndDate": current_date_iso8601,
    }
    # Act
    cves = get_modified_cves(mock_session, NIST_CVE_URL, last_modified_date_iso8601, API_KEY)
    # Assert
    mock_call_cves_api.assert_called_once_with(mock_session, NIST_CVE_URL, API_KEY, expected_params)
    assert cves == GET_CVE_API_DATA


@patch("cartography.intel.cve.feed._call_cves_api")
def test_get_published_cves_per_year(mock_call_cves_api: Mock, mock_session: Session):
    # Arrange
    no_cves = {
        "resultsPerPage": 0,
        "startIndex": 4000,
        "totalResults": 4000,
        "format": "NVD_CVE",
        "version": "2.0",
        "timestamp": "2024-01-10T19:30:07.520",
        "vulnerabilities": [],
    }
    expected_cves = GET_CVE_API_DATA.copy()
    _map_cve_dict(expected_cves, no_cves)
    mock_call_cves_api.side_effect = [GET_CVE_API_DATA, no_cves, no_cves, no_cves]
    # Act
    cves = get_published_cves_per_year(mock_session, NIST_CVE_URL, "2024", API_KEY)
    # Assert
    assert mock_call_cves_api.call_count == 4
    assert cves == expected_cves
