from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

import cartography.intel.gcp
from cartography.analysis.gcp.analysis import GCP_COMPUTE_CLOUDRUN_EXPOSURE
from cartography.analysis.gcp.analysis import GCP_COMPUTE_FIREWALL_INGRESS
from cartography.analysis.gcp.analysis import GCP_COMPUTE_FORWARDING_RULE_EXPOSURE
from cartography.analysis.gcp.analysis import GCP_COMPUTE_INSTANCE_EXPOSURE
from cartography.analysis.gcp.analysis import GCP_LB_EXPOSURE


def _make_serviceusage_client(enabled_services: list[str]) -> MagicMock:
    client = MagicMock()
    request = MagicMock()
    request.execute.return_value = {
        "services": [{"config": {"name": name}} for name in enabled_services]
    }
    client.services.return_value.list.return_value = request
    client.services.return_value.list_next.return_value = None
    return client


def test_iam_syncs_before_compute_so_runs_as_can_match():
    """
    Within a project sync, IAM must run before Compute so that the
    GCPServiceAccount nodes exist when Compute creates the
    GCPInstance-[:RUNS_AS]->GCPServiceAccount edge (which matches on the
    service account email). This guards the ordering in _sync_project_resources.
    """
    common_job_parameters = {"UPDATE_TAG": 123}
    credentials = MagicMock()
    neo4j_session = MagicMock()

    serviceusage_client = _make_serviceusage_client(
        ["compute.googleapis.com", "iam.googleapis.com"]
    )

    def _build_client(service_name, version, credentials):
        if service_name == "serviceusage":
            return serviceusage_client
        # The compute/iam clients are not exercised here because we patch the
        # corresponding sync() functions below.
        return MagicMock()

    call_order: list[str] = []

    def _record_iam_sync(*args, **kwargs):
        call_order.append("iam")
        return []

    def _record_compute_sync(*args, **kwargs):
        call_order.append("compute")

    with (
        patch("cartography.intel.gcp.build_client", side_effect=_build_client),
        patch.object(cartography.intel.gcp.iam, "sync", side_effect=_record_iam_sync),
        patch.object(
            cartography.intel.gcp.iam,
            "build_role_permissions_by_name",
            return_value={},
        ),
        patch.object(cartography.intel.gcp.workload_identity, "sync"),
        patch.object(
            cartography.intel.gcp.compute, "sync", side_effect=_record_compute_sync
        ),
        patch.object(cartography.intel.gcp.iam, "cleanup_service_account_keys"),
        patch.object(cartography.intel.gcp.iam, "cleanup_service_accounts"),
        patch.object(cartography.intel.gcp.iam, "cleanup_project_roles"),
        patch.object(cartography.intel.gcp, "run_typed_analysis_job"),
    ):
        cartography.intel.gcp._sync_project_resources(
            neo4j_session,
            [{"projectId": "test-project"}],
            123,
            common_job_parameters,
            credentials,
            requested_syncs={"compute", "iam"},
        )

    assert call_order == ["iam", "compute"]


@pytest.mark.parametrize(
    "requested_syncs, expected_jobs",
    [
        pytest.param(
            {"cloud_run"},
            [GCP_COMPUTE_CLOUDRUN_EXPOSURE],
            id="cloud_run_only",
        ),
        pytest.param(
            {"compute"},
            [
                GCP_COMPUTE_FORWARDING_RULE_EXPOSURE,
                GCP_COMPUTE_FIREWALL_INGRESS,
                GCP_COMPUTE_INSTANCE_EXPOSURE,
                GCP_LB_EXPOSURE,
            ],
            id="compute_only",
        ),
    ],
)
def test_exposure_jobs_follow_the_sync_that_feeds_them(requested_syncs, expected_jobs):
    """
    Exposure flags survive ingestion, so each exposure job must run whenever its
    input data is refreshed. Cloud Run exposure reads only Cloud Run services.
    """
    serviceusage_client = _make_serviceusage_client([])

    with (
        patch("cartography.intel.gcp.build_client", return_value=serviceusage_client),
        patch.object(cartography.intel.gcp, "run_typed_analysis_job") as run_job,
    ):
        cartography.intel.gcp._sync_project_resources(
            MagicMock(),
            [{"projectId": "test-project"}],
            123,
            {"UPDATE_TAG": 123},
            MagicMock(),
            requested_syncs=requested_syncs,
        )

    assert [call.args[0] for call in run_job.call_args_list] == expected_jobs
