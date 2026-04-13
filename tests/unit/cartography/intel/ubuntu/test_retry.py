from unittest.mock import MagicMock
from unittest.mock import patch

from requests import Session
from requests.adapters import HTTPAdapter
from urllib3 import Retry

from cartography.intel.ubuntu.util import retryable_session


class TestRetryableSession:
    def test_returns_session_instance(self):
        session = retryable_session()
        assert isinstance(session, Session)

    def test_mounts_https_adapter_with_retry(self):
        session = retryable_session()
        adapter = session.get_adapter("https://ubuntu.com")
        assert isinstance(adapter, HTTPAdapter)
        retry: Retry = adapter.max_retries
        assert isinstance(retry, Retry)

    def test_retry_policy_covers_503(self):
        session = retryable_session()
        retry: Retry = session.get_adapter("https://example.com").max_retries
        assert 503 in retry.status_forcelist

    def test_retry_policy_parameters(self):
        session = retryable_session()
        retry: Retry = session.get_adapter("https://example.com").max_retries
        assert retry.total == 5
        assert retry.connect == 1
        assert retry.backoff_factor == 1
        assert set(retry.status_forcelist) == {429, 500, 502, 503, 504}
        assert set(retry.allowed_methods) == {"GET"}


class TestFetchUsesRetrySession:
    @patch("cartography.intel.ubuntu.cves.retryable_session")
    def test_fetch_cves_creates_retryable_session(self, mock_factory):
        mock_session = MagicMock(spec=Session)
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"cves": [], "total_results": 0}
        mock_session.get.return_value = mock_response
        mock_factory.return_value = mock_session

        from cartography.intel.ubuntu.cves import _fetch_cves

        list(_fetch_cves("https://ubuntu.com"))
        mock_factory.assert_called_once()

    @patch("cartography.intel.ubuntu.notices.retryable_session")
    def test_fetch_notices_creates_retryable_session(self, mock_factory):
        mock_session = MagicMock(spec=Session)
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"notices": [], "total_results": 0}
        mock_session.get.return_value = mock_response
        mock_factory.return_value = mock_session

        from cartography.intel.ubuntu.notices import _fetch_notices

        list(_fetch_notices("https://ubuntu.com"))
        mock_factory.assert_called_once()
