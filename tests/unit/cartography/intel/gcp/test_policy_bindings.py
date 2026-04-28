import logging
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from google.api_core.exceptions import PermissionDenied
from google.api_core.exceptions import ResourceExhausted
from google.api_core.exceptions import RetryError

import cartography.intel.gcp
import cartography.intel.gcp.policy_bindings as policy_bindings
from cartography.intel.gcp.policy_bindings import _parse_full_resource_name

TEST_PROJECT_ID = "project-abc"
TEST_UPDATE_TAG = 123456789
COMMON_JOB_PARAMS = {
    "UPDATE_TAG": TEST_UPDATE_TAG,
    "ORG_RESOURCE_NAME": "organizations/1337",
    "PROJECT_ID": TEST_PROJECT_ID,
}


@pytest.mark.parametrize(
    "full_name, expected",
    [
        # CRM
        (
            "//cloudresourcemanager.googleapis.com/projects/project-abc",
            ("GCPProject", "project-abc"),
        ),
        (
            "//cloudresourcemanager.googleapis.com/folders/1414",
            ("GCPFolder", "folders/1414"),
        ),
        (
            "//cloudresourcemanager.googleapis.com/organizations/1337",
            ("GCPOrganization", "organizations/1337"),
        ),
        # Storage
        (
            "//storage.googleapis.com/buckets/test-bucket",
            ("GCPBucket", "test-bucket"),
        ),
        # Storage sub-resource resolves to owning bucket
        (
            "//storage.googleapis.com/buckets/test-bucket/objects/foo.txt",
            ("GCPBucket", "test-bucket"),
        ),
        # KMS — cryptoKey wins over keyRing
        (
            "//cloudkms.googleapis.com/projects/p/locations/us/keyRings/r/cryptoKeys/k",
            ("GCPCryptoKey", "projects/p/locations/us/keyRings/r/cryptoKeys/k"),
        ),
        # KMS — plain keyRing
        (
            "//cloudkms.googleapis.com/projects/p/locations/us/keyRings/r",
            ("GCPKeyRing", "projects/p/locations/us/keyRings/r"),
        ),
        # KMS — cryptoKey version resolves up to the cryptoKey
        (
            "//cloudkms.googleapis.com/projects/p/locations/us/keyRings/r/cryptoKeys/k/cryptoKeyVersions/1",
            ("GCPCryptoKey", "projects/p/locations/us/keyRings/r/cryptoKeys/k"),
        ),
        # Secret Manager — version wins over secret
        (
            "//secretmanager.googleapis.com/projects/p/secrets/s/versions/1",
            (
                "GCPSecretManagerSecretVersion",
                "projects/p/secrets/s/versions/1",
            ),
        ),
        # Secret Manager — plain secret
        (
            "//secretmanager.googleapis.com/projects/p/secrets/s",
            ("GCPSecretManagerSecret", "projects/p/secrets/s"),
        ),
        # Artifact Registry
        (
            "//artifactregistry.googleapis.com/projects/p/locations/us/repositories/r",
            (
                "GCPArtifactRegistryRepository",
                "projects/p/locations/us/repositories/r",
            ),
        ),
        # Cloud Run service
        (
            "//run.googleapis.com/projects/p/locations/us-central1/services/svc",
            (
                "GCPCloudRunService",
                "projects/p/locations/us-central1/services/svc",
            ),
        ),
        # Compute — instance (partial_uri format)
        (
            "//compute.googleapis.com/projects/p/zones/us-central1-a/instances/vm1",
            ("GCPInstance", "projects/p/zones/us-central1-a/instances/vm1"),
        ),
        # Compute — VPC
        (
            "//compute.googleapis.com/projects/p/global/networks/default",
            ("GCPVpc", "projects/p/global/networks/default"),
        ),
        # Compute — subnet
        (
            "//compute.googleapis.com/projects/p/regions/us-central1/subnetworks/sub",
            ("GCPSubnet", "projects/p/regions/us-central1/subnetworks/sub"),
        ),
        # Compute — firewall
        (
            "//compute.googleapis.com/projects/p/global/firewalls/fw-allow-ssh",
            ("GCPFirewall", "projects/p/global/firewalls/fw-allow-ssh"),
        ),
        # Unknown service
        (
            "//bigquery.googleapis.com/projects/p/datasets/d",
            (None, None),
        ),
        # Empty suffix
        (
            "//cloudresourcemanager.googleapis.com/projects/",
            (None, None),
        ),
        # Marker absent from path
        (
            "//storage.googleapis.com/something-else/foo",
            (None, None),
        ),
    ],
)
def test_parse_full_resource_name(full_name, expected):
    assert _parse_full_resource_name(full_name) == expected


def test_wait_for_cai_policy_bindings_slot_reserves_per_operation_slots():
    original_state = policy_bindings._CAI_POLICY_BINDINGS_LAST_CALL_BY_OPERATION.copy()
    policy_bindings._CAI_POLICY_BINDINGS_LAST_CALL_BY_OPERATION.clear()
    try:
        with (
            patch.object(policy_bindings.time, "monotonic", return_value=100.0),
            patch.object(policy_bindings.time, "sleep") as mock_sleep,
        ):
            policy_bindings._wait_for_cai_policy_bindings_slot(
                "search_all_iam_policies"
            )
            policy_bindings._wait_for_cai_policy_bindings_slot(
                "search_all_iam_policies"
            )
            policy_bindings._wait_for_cai_policy_bindings_slot(
                "batch_get_effective_iam_policies"
            )

        assert mock_sleep.call_count == 1
        assert mock_sleep.call_args.args[0] == pytest.approx(0.2)
        assert policy_bindings._CAI_POLICY_BINDINGS_LAST_CALL_BY_OPERATION[
            "search_all_iam_policies"
        ] == pytest.approx(100.4)
        assert policy_bindings._CAI_POLICY_BINDINGS_LAST_CALL_BY_OPERATION[
            "batch_get_effective_iam_policies"
        ] == pytest.approx(100.75)
    finally:
        policy_bindings._CAI_POLICY_BINDINGS_LAST_CALL_BY_OPERATION.clear()
        policy_bindings._CAI_POLICY_BINDINGS_LAST_CALL_BY_OPERATION.update(
            original_state
        )


@patch.object(policy_bindings, "_wait_for_cai_policy_bindings_slot")
@patch.object(policy_bindings, "MessageToDict")
def test_get_policy_bindings_passes_custom_retry_to_cai_rpcs(
    mock_message_to_dict,
    mock_wait_for_slot,
):
    client = MagicMock()
    client.batch_get_effective_iam_policies.return_value = MagicMock(_pb=object())

    search_page = MagicMock()
    search_page.results = [MagicMock(_pb=object())]
    search_page.next_page_token = ""
    search_pager = MagicMock()
    search_pager.pages = [search_page]
    client.search_all_iam_policies.return_value = search_pager

    mock_message_to_dict.side_effect = [
        {
            "policy_results": [
                {
                    "full_resource_name": f"//cloudresourcemanager.googleapis.com/projects/{TEST_PROJECT_ID}",
                    "policies": [],
                },
            ],
        },
        {
            "resource": "//storage.googleapis.com/buckets/test-bucket",
            "policy": {"bindings": [{"role": "roles/storage.objectViewer"}]},
        },
    ]

    result = policy_bindings.get_policy_bindings(
        TEST_PROJECT_ID,
        COMMON_JOB_PARAMS,
        client,
    )

    assert len(result["policy_results"]) == 2
    batch_retry = client.batch_get_effective_iam_policies.call_args.kwargs["retry"]
    search_retry = client.search_all_iam_policies.call_args.kwargs["retry"]

    assert batch_retry._predicate(ResourceExhausted("quota exceeded")) is True
    assert search_retry._predicate(ResourceExhausted("quota exceeded")) is True
    assert batch_retry._predicate(PermissionDenied("forbidden")) is False
    assert search_retry._predicate(PermissionDenied("forbidden")) is False

    assert (
        client.batch_get_effective_iam_policies.call_args.kwargs["timeout"]
        == policy_bindings.CAI_POLICY_BINDINGS_BATCH_TIMEOUT
    )
    assert (
        client.search_all_iam_policies.call_args.kwargs["timeout"]
        == policy_bindings.CAI_POLICY_BINDINGS_SEARCH_TIMEOUT
    )
    assert mock_wait_for_slot.call_count == 2


@patch.object(policy_bindings, "cleanup")
@patch.object(policy_bindings, "load_bindings")
@patch.object(
    policy_bindings,
    "get_policy_bindings",
    side_effect=RetryError(
        "Cloud Asset policy bindings retry budget exhausted",
        ResourceExhausted("429 quota exceeded"),
    ),
)
def test_sync_skips_load_and_cleanup_on_rate_limit_retry_exhaustion(
    mock_get_policy_bindings,
    mock_load_bindings,
    mock_cleanup,
    caplog,
):
    with caplog.at_level(logging.WARNING):
        result = policy_bindings.sync(
            MagicMock(),
            TEST_PROJECT_ID,
            TEST_UPDATE_TAG,
            COMMON_JOB_PARAMS,
            MagicMock(),
            {},
        )

    assert result.status == policy_bindings.PolicyBindingsSyncStatus.SKIPPED_RATE_LIMIT
    mock_get_policy_bindings.assert_called_once()
    mock_load_bindings.assert_not_called()
    mock_cleanup.assert_not_called()
    assert any("retries exhausted" in record.message for record in caplog.records)
    assert any(
        "Preserving existing policy-binding" in record.message
        for record in caplog.records
    )


@patch("cartography.intel.gcp.build_asset_client")
@patch("cartography.intel.gcp.build_client")
@patch("cartography.intel.gcp.permission_relationships.sync")
@patch(
    "cartography.intel.gcp.policy_bindings.sync",
    return_value=policy_bindings.PolicyBindingsSyncResult(
        policy_bindings.PolicyBindingsSyncStatus.SKIPPED_RATE_LIMIT,
        {},
    ),
)
@patch(
    "cartography.intel.gcp._services_enabled_on_project",
    side_effect=[set(), {cartography.intel.gcp.service_names.cai}],
)
def test_sync_project_resources_skips_permission_relationships_after_policy_binding_rate_limit(
    mock_services_enabled,
    mock_policy_bindings_sync,
    mock_permission_relationships_sync,
    mock_build_client,
    mock_build_asset_client,
):
    mock_build_client.return_value = MagicMock()
    mock_build_asset_client.return_value = MagicMock()

    cartography.intel.gcp._sync_project_resources(
        neo4j_session=MagicMock(),
        projects=[{"projectId": TEST_PROJECT_ID}],
        gcp_update_tag=TEST_UPDATE_TAG,
        common_job_parameters=COMMON_JOB_PARAMS.copy(),
        credentials=MagicMock(),
        requested_syncs={"policy_bindings", "permission_relationships"},
    )

    assert mock_services_enabled.call_count == 2
    mock_policy_bindings_sync.assert_called_once()
    mock_permission_relationships_sync.assert_not_called()


@patch("cartography.intel.gcp.build_asset_client")
@patch("cartography.intel.gcp.build_client")
@patch("cartography.intel.gcp.permission_relationships.sync")
@patch("cartography.intel.gcp.policy_bindings.sync")
@patch(
    "cartography.intel.gcp._services_enabled_on_project",
    side_effect=[set(), set()],
)
def test_sync_project_resources_skips_permission_relationships_when_cai_api_disabled(
    mock_services_enabled,
    mock_policy_bindings_sync,
    mock_permission_relationships_sync,
    mock_build_client,
    mock_build_asset_client,
):
    mock_build_client.return_value = MagicMock()
    mock_build_asset_client.return_value = MagicMock()

    cartography.intel.gcp._sync_project_resources(
        neo4j_session=MagicMock(),
        projects=[{"projectId": TEST_PROJECT_ID}],
        gcp_update_tag=TEST_UPDATE_TAG,
        common_job_parameters=COMMON_JOB_PARAMS.copy(),
        credentials=MagicMock(),
        requested_syncs={"policy_bindings", "permission_relationships"},
    )

    assert mock_services_enabled.call_count == 2
    mock_policy_bindings_sync.assert_not_called()
    mock_permission_relationships_sync.assert_not_called()
