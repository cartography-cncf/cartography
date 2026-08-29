import json
from unittest.mock import MagicMock

import pytest
from googleapiclient.errors import HttpError

from cartography.intel.gcp import workload_identity


def _make_http_error(status: int = 403, reason: str | None = None) -> HttpError:
    resp = MagicMock()
    resp.status = status
    payload: dict = {"error": {"code": status}}
    if reason:
        payload["error"]["errors"] = [{"reason": reason}]
    return HttpError(resp=resp, content=json.dumps(payload).encode("utf-8"))


def test_sync_skips_billing_disabled_pool_listing(monkeypatch):
    error = _make_http_error(403, "BILLING_DISABLED")

    monkeypatch.setattr(
        workload_identity,
        "get_workload_identity_pools",
        lambda _iam_client, _project_id: (_ for _ in ()).throw(error),
    )

    workload_identity.sync(
        neo4j_session=MagicMock(),
        iam_client=MagicMock(),
        project_id="test-project",
        gcp_update_tag=1,
        common_job_parameters={"UPDATE_TAG": 1, "PROJECT_ID": "test-project"},
    )


def test_sync_skips_quota_403_pool_listing(monkeypatch):
    error = _make_http_error(403, "rateLimitExceeded")

    monkeypatch.setattr(
        workload_identity,
        "get_workload_identity_pools",
        lambda _iam_client, _project_id: (_ for _ in ()).throw(error),
    )

    workload_identity.sync(
        neo4j_session=MagicMock(),
        iam_client=MagicMock(),
        project_id="test-project",
        gcp_update_tag=1,
        common_job_parameters={"UPDATE_TAG": 1, "PROJECT_ID": "test-project"},
    )


def test_sync_reraises_non_403_transient_pool_listing(monkeypatch):
    error = _make_http_error(503, "backendError")

    monkeypatch.setattr(
        workload_identity,
        "get_workload_identity_pools",
        lambda _iam_client, _project_id: (_ for _ in ()).throw(error),
    )

    with pytest.raises(HttpError):
        workload_identity.sync(
            neo4j_session=MagicMock(),
            iam_client=MagicMock(),
            project_id="test-project",
            gcp_update_tag=1,
            common_job_parameters={"UPDATE_TAG": 1, "PROJECT_ID": "test-project"},
        )
