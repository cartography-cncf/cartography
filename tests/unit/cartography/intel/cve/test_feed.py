from datetime import datetime
from datetime import timedelta
from datetime import timezone
from unittest.mock import Mock
from unittest.mock import patch

import requests

from cartography.intel.cve.feed import _call_cves_api
from cartography.intel.cve.feed import _map_cve_dict
from cartography.intel.cve.feed import get_cves_in_batches
from cartography.intel.cve.feed import get_modified_cves
from cartography.intel.cve.feed import get_published_cves_per_year
from tests.data.cve.feed import GET_CVE_API_DATA
from tests.data.cve.feed import GET_CVE_API_DATA_BATCH_2

NIST_CVE_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0/"
API_KEY = "nvd_api_key"


@patch("cartography.intel.cve.feed.DEFAULT_SLEEP_TIME", 0)
@patch("cartography.intel.cve.feed.requests.get")
def test_call_cves_api(mock_get: Mock):
    # Arrange
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

    mock_get.side_effect = [mock_response_1, mock_response_2, mock_response_3]
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
    result = _call_cves_api(NIST_CVE_URL, API_KEY, params)

    # Assert
    assert mock_get.call_count == 3
    assert result == expected_result


@patch("cartography.intel.cve.feed.DEFAULT_SLEEP_TIME", 0)
@patch("cartography.intel.cve.feed.requests.get")
def test_call_cves_api_with_error(mock_get: Mock):
    # Arrange
    mock_response = Mock()
    mock_response.status_code = 404
    mock_response.message = "Data error"
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
        response=mock_response,
    )
    mock_get.return_value = mock_response
    params = {"start": "2024-01-10T00:00:00Z", "end": "2024-01-10T23:59:59Z"}

    # Act
    try:
        _call_cves_api(NIST_CVE_URL, API_KEY, params)
    except requests.exceptions.HTTPError as err:
        assert err.response == mock_response
    assert mock_get.call_count == 3


@patch("cartography.intel.cve.feed._call_cves_api")
def test_get_cves_in_batches(mock_call_cves_api: Mock):
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
        NIST_CVE_URL, start_date, end_date, date_param_names, API_KEY,
    )
    # Assert
    assert mock_call_cves_api.call_count == 2
    assert cves == excepted_cves


@patch("cartography.intel.cve.feed._call_cves_api")
def test_get_modified_cves(mock_call_cves_api: Mock):
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
    cves = get_modified_cves(NIST_CVE_URL, last_modified_date_iso8601, API_KEY)
    # Assert
    mock_call_cves_api.assert_called_once_with(NIST_CVE_URL, API_KEY, expected_params)
    assert cves == GET_CVE_API_DATA


@patch("cartography.intel.cve.feed._call_cves_api")
def test_get_published_cves_per_year(mock_call_cves_api: Mock):
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
    cves = get_published_cves_per_year(NIST_CVE_URL, "2024", API_KEY)
    # Assert
    mock_call_cves_api.call_count == 4
    assert cves == expected_cves
