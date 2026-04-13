import logging
from unittest.mock import Mock

import pytest
from requests import Session
from requests.adapters import HTTPAdapter
from urllib3.exceptions import MaxRetryError

from cartography.intel.ubuntu.util import LoggingRetry
from cartography.intel.ubuntu.util import retryable_session


class TestRetryableSession:
    def test_returns_session_instance(self):
        session = retryable_session()
        assert isinstance(session, Session)

    def test_mounts_https_adapter_with_retry(self):
        session = retryable_session()
        adapter = session.get_adapter("https://ubuntu.com")
        assert isinstance(adapter, HTTPAdapter)
        assert isinstance(adapter.max_retries, LoggingRetry)

    def test_retry_policy_covers_503(self):
        session = retryable_session()
        retry = session.get_adapter("https://example.com").max_retries
        assert 503 in retry.status_forcelist

    def test_retry_policy_parameters(self):
        session = retryable_session()
        retry = session.get_adapter("https://example.com").max_retries
        assert retry.total == 5
        assert retry.connect == 1
        assert retry.backoff_factor == 1
        assert set(retry.status_forcelist) == {429, 500, 502, 503, 504}
        assert set(retry.allowed_methods) == {"GET"}


class TestLoggingRetry:
    def test_logs_warning_on_retry(self, caplog):
        retry = LoggingRetry(total=3, status_forcelist=[503], allowed_methods=["GET"])
        mock_response = Mock(status=503)

        with caplog.at_level(logging.WARNING, logger="cartography.intel.ubuntu.util"):
            retry.increment(
                method="GET",
                url="/security/cves.json",
                response=mock_response,
            )

        assert len(caplog.records) == 1
        assert "Ubuntu API retry" in caplog.records[0].message
        assert "503" in caplog.records[0].message

    def test_logs_error_when_retries_exhausted(self, caplog):
        retry = LoggingRetry(total=0, status_forcelist=[503], allowed_methods=["GET"])
        mock_response = Mock(status=503)

        with caplog.at_level(logging.WARNING, logger="cartography.intel.ubuntu.util"):
            with pytest.raises(MaxRetryError):
                retry.increment(
                    method="GET",
                    url="/security/cves.json",
                    response=mock_response,
                )

        error_records = [r for r in caplog.records if r.levelno == logging.ERROR]
        assert len(error_records) == 1
        assert "retries exhausted" in error_records[0].message
