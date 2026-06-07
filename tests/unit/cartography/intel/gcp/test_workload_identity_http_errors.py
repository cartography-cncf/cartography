from unittest.mock import MagicMock

from googleapiclient.errors import HttpError

from cartography.intel.gcp import workload_identity


def _make_http_error(status: int = 403) -> HttpError:
    resp = MagicMock()
    resp.status = status
    return HttpError(resp=resp, content=b"{}")


def test_sync_skips_billing_disabled_pool_listing(monkeypatch):
    error = _make_http_error()

    monkeypatch.setattr(
        workload_identity,
        "get_workload_identity_pools",
        lambda _iam_client, _project_id: (_ for _ in ()).throw(error),
    )
    monkeypatch.setattr(
        workload_identity,
        "classify_gcp_http_error",
        lambda _error: "billing_disabled",
    )

    workload_identity.sync(
        neo4j_session=MagicMock(),
        iam_client=MagicMock(),
        project_id="test-project",
        gcp_update_tag=1,
        common_job_parameters={"UPDATE_TAG": 1, "PROJECT_ID": "test-project"},
    )
