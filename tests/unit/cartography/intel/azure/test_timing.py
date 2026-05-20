"""
Unit tests for cartography.intel.azure.util.timing and the timing instrumentation
added to _sync_one_subscription / concurrent_execution.
"""
import json
import logging
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from cartography.intel.azure.util.timing import AzureTimingPolicy
from cartography.intel.azure.util.timing import get_current_context
from cartography.intel.azure.util.timing import get_timing_policy
from cartography.intel.azure.util.timing import ServiceTimingContext


# ---------------------------------------------------------------------------
# ServiceTimingContext
# ---------------------------------------------------------------------------

class TestServiceTimingContext:
    def test_sets_and_clears_thread_local(self):
        assert get_current_context() is None
        with ServiceTimingContext("svc") as ctx:
            assert get_current_context() is ctx
            assert ctx.service_name == "svc"
        assert get_current_context() is None

    def test_clears_on_exception(self):
        try:
            with ServiceTimingContext("svc"):
                raise ValueError("boom")
        except ValueError:
            pass
        assert get_current_context() is None

    def test_initial_counts_are_zero(self):
        with ServiceTimingContext("svc") as ctx:
            assert ctx.to_dict() == {"request_count": 0, "throttle_count": 0, "retry_count": 0}

    def test_to_dict_reflects_mutations(self):
        with ServiceTimingContext("svc") as ctx:
            ctx.request_count = 5
            ctx.throttle_count = 2
            ctx.retry_count = 1
            d = ctx.to_dict()
        assert d == {"request_count": 5, "throttle_count": 2, "retry_count": 1}

    def test_nested_context_replaces_outer(self):
        with ServiceTimingContext("outer") as outer_ctx:
            with ServiceTimingContext("inner") as inner_ctx:
                assert get_current_context() is inner_ctx
            # inner __exit__ clears the thread-local; outer context is now orphaned
            assert get_current_context() is None
        _ = outer_ctx  # still accessible as a plain object, just not in thread-local


# ---------------------------------------------------------------------------
# AzureTimingPolicy
# ---------------------------------------------------------------------------

def _mock_request():
    return MagicMock()


def _mock_response(status_code: int, headers: dict = None):
    resp = MagicMock()
    resp.http_response.status_code = status_code
    resp.http_response.headers = headers or {}
    return resp


class TestAzureTimingPolicy:
    def test_on_request_increments_count(self):
        policy = AzureTimingPolicy()
        with ServiceTimingContext("svc") as ctx:
            policy.on_request(_mock_request())
            policy.on_request(_mock_request())
            assert ctx.request_count == 2

    def test_on_request_noop_without_context(self):
        policy = AzureTimingPolicy()
        assert get_current_context() is None
        policy.on_request(_mock_request())  # must not raise

    def test_throttle_detected_on_429(self):
        policy = AzureTimingPolicy()
        with ServiceTimingContext("svc") as ctx:
            policy.on_response(_mock_request(), _mock_response(429))
            assert ctx.throttle_count == 1

    def test_no_throttle_on_200(self):
        policy = AzureTimingPolicy()
        with ServiceTimingContext("svc") as ctx:
            policy.on_response(_mock_request(), _mock_response(200))
            assert ctx.throttle_count == 0

    def test_retry_counted_on_retry_after_header(self):
        policy = AzureTimingPolicy()
        with ServiceTimingContext("svc") as ctx:
            policy.on_response(_mock_request(), _mock_response(429, {"Retry-After": "5"}))
            assert ctx.retry_count == 1

    def test_retry_counted_on_ms_retry_header(self):
        policy = AzureTimingPolicy()
        with ServiceTimingContext("svc") as ctx:
            policy.on_response(_mock_request(), _mock_response(429, {"x-ms-retry-after-ms": "2000"}))
            assert ctx.retry_count == 1

    def test_no_retry_without_retry_header(self):
        policy = AzureTimingPolicy()
        with ServiceTimingContext("svc") as ctx:
            policy.on_response(_mock_request(), _mock_response(200, {}))
            assert ctx.retry_count == 0

    def test_on_response_noop_without_context(self):
        policy = AzureTimingPolicy()
        assert get_current_context() is None
        policy.on_response(_mock_request(), _mock_response(429))  # must not raise

    def test_get_timing_policy_returns_singleton(self):
        assert get_timing_policy() is get_timing_policy()

    def test_policy_is_stateless_across_contexts(self):
        policy = AzureTimingPolicy()
        with ServiceTimingContext("first") as ctx1:
            policy.on_request(_mock_request())
        with ServiceTimingContext("second") as ctx2:
            policy.on_request(_mock_request())
        assert ctx1.request_count == 1
        assert ctx2.request_count == 1


# ---------------------------------------------------------------------------
# _sync_one_subscription — sequential run timing logs
# ---------------------------------------------------------------------------

def _make_credentials():
    creds = MagicMock()
    creds.tenant_id = "tenant-abc"
    creds.arm_credentials = MagicMock()
    return creds


def _make_config(regions=None):
    cfg = MagicMock()
    cfg.params = {"regions": regions}
    return cfg


def _collect_timing_events(caplog_records, event_name):
    events = []
    for record in caplog_records:
        try:
            data = json.loads(record.message)
            if data.get("event") == event_name:
                events.append(data)
        except (json.JSONDecodeError, AttributeError):
            pass
    return events


@pytest.fixture()
def mock_tag_sync():
    with patch("cartography.intel.azure.tag.sync") as m:
        yield m


class TestSyncOneSubscriptionSequential:
    """Sequential run (LOCAL_RUN=1) timing log assertions."""

    @patch.dict("os.environ", {"LOCAL_RUN": "1"})
    def test_success_log_has_required_fields(self, caplog, mock_tag_sync):
        mock_func = MagicMock()
        with patch("cartography.intel.azure.RESOURCE_FUNCTIONS", {"compute": mock_func}):
            from cartography.intel.azure import _sync_one_subscription
            with caplog.at_level(logging.INFO, logger="cartography.intel.azure"):
                _sync_one_subscription(
                    neo4j_session=MagicMock(),
                    credentials=_make_credentials(),
                    subscription_id="sub-001",
                    tenant={"defaultDomain": "test.onmicrosoft.com"},
                    requested_syncs=["compute"],
                    update_tag=1,
                    common_job_parameters={},
                    config=_make_config(),
                )

        events = _collect_timing_events(caplog.records, "azure_service_timing")
        assert len(events) == 1
        e = events[0]
        assert e["service"] == "compute"
        assert e["subscription_id"] == "sub-001"
        assert e["run_mode"] == "sequential"
        assert e["status"] == "success"
        assert isinstance(e["duration_seconds"], float)
        assert "request_count" in e
        assert "throttle_count" in e
        assert "retry_count" in e

    @patch.dict("os.environ", {"LOCAL_RUN": "1"})
    def test_error_path_timing_still_logged(self, caplog, mock_tag_sync):
        failing_func = MagicMock(side_effect=RuntimeError("azure down"))
        with patch("cartography.intel.azure.RESOURCE_FUNCTIONS", {"storage": failing_func}):
            from cartography.intel.azure import _sync_one_subscription
            with caplog.at_level(logging.INFO, logger="cartography.intel.azure"):
                _sync_one_subscription(
                    neo4j_session=MagicMock(),
                    credentials=_make_credentials(),
                    subscription_id="sub-002",
                    tenant={"defaultDomain": "test.onmicrosoft.com"},
                    requested_syncs=["storage"],
                    update_tag=1,
                    common_job_parameters={},
                    config=_make_config(),
                )

        events = _collect_timing_events(caplog.records, "azure_service_timing")
        assert len(events) == 1
        e = events[0]
        assert e["status"] == "error"
        assert e["error_type"] == "RuntimeError"
        assert e["error_message"] == "azure down"
        assert isinstance(e["duration_seconds"], float)

    @patch.dict("os.environ", {"LOCAL_RUN": "1"})
    def test_summary_has_run_mode_and_failed_services(self, caplog, mock_tag_sync):
        ok_func = MagicMock()
        fail_func = MagicMock(side_effect=ValueError("boom"))
        with patch("cartography.intel.azure.RESOURCE_FUNCTIONS", {"compute": ok_func, "sql": fail_func}):
            from cartography.intel.azure import _sync_one_subscription
            with caplog.at_level(logging.INFO, logger="cartography.intel.azure"):
                _sync_one_subscription(
                    neo4j_session=MagicMock(),
                    credentials=_make_credentials(),
                    subscription_id="sub-003",
                    tenant={"defaultDomain": "test.onmicrosoft.com"},
                    requested_syncs=["compute", "sql"],
                    update_tag=1,
                    common_job_parameters={},
                    config=_make_config(),
                )

        summaries = _collect_timing_events(caplog.records, "azure_subscription_timing_summary")
        assert len(summaries) == 1
        s = summaries[0]
        assert s["run_mode"] == "sequential"
        assert "sql" in s["failed_services"]
        assert s["failed_services"]["sql"] == "ValueError"
        assert "compute" not in s["failed_services"]
        assert isinstance(s["total_duration_seconds"], float)

    @patch.dict("os.environ", {"LOCAL_RUN": "1"})
    def test_all_services_succeed_empty_failed_services(self, caplog, mock_tag_sync):
        with patch("cartography.intel.azure.RESOURCE_FUNCTIONS", {"compute": MagicMock()}):
            from cartography.intel.azure import _sync_one_subscription
            with caplog.at_level(logging.INFO, logger="cartography.intel.azure"):
                _sync_one_subscription(
                    neo4j_session=MagicMock(),
                    credentials=_make_credentials(),
                    subscription_id="sub-004",
                    tenant={"defaultDomain": "test.onmicrosoft.com"},
                    requested_syncs=["compute"],
                    update_tag=1,
                    common_job_parameters={},
                    config=_make_config(),
                )

        summaries = _collect_timing_events(caplog.records, "azure_subscription_timing_summary")
        assert summaries[0]["failed_services"] == {}
