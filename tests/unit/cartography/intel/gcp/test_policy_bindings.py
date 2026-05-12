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
        # BigQuery dataset
        (
            "//bigquery.googleapis.com/projects/project-abc/datasets/dataset_a",
            ("GCPBigQueryDataset", "project-abc:dataset_a"),
        ),
        # BigQuery table
        (
            "//bigquery.googleapis.com/projects/project-abc/datasets/dataset_a/tables/events",
            ("GCPBigQueryTable", "project-abc:dataset_a.events"),
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
        # Service Account
        (
            "//iam.googleapis.com/projects/project-abc/serviceAccounts/sa@project-abc.iam.gserviceaccount.com",
            ("GCPServiceAccount", "sa@project-abc.iam.gserviceaccount.com"),
        ),
        # Cloud Functions
        (
            "//cloudfunctions.googleapis.com/projects/p/locations/us-central1/functions/fn",
            ("GCPCloudFunction", "projects/p/locations/us-central1/functions/fn"),
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
            "//pubsub.googleapis.com/projects/p/topics/t",
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


def test_policy_bindings_search_asset_types_come_from_full_name_mappings():
    assert policy_bindings.GCP_POLICY_BINDINGS_SEARCH_ASSET_TYPES == [
        asset_type
        for mapping in policy_bindings._FULL_NAME_MAPPINGS
        for asset_type in (
            ((mapping.asset_type,) if mapping.asset_type is not None else ())
            + mapping.additional_asset_types
        )
    ]
    assert (
        "artifactregistry.googleapis.com/Repository"
        in policy_bindings.GCP_POLICY_BINDINGS_SEARCH_ASSET_TYPES
    )
    assert (
        "cloudfunctions.googleapis.com/Function"
        in policy_bindings.GCP_POLICY_BINDINGS_SEARCH_ASSET_TYPES
    )
    assert (
        "cloudfunctions.googleapis.com/CloudFunction"
        in policy_bindings.GCP_POLICY_BINDINGS_SEARCH_ASSET_TYPES
    )
    assert (
        "artifactregistry.googleapis.com/DockerImage"
        not in policy_bindings.GCP_POLICY_BINDINGS_SEARCH_ASSET_TYPES
    )


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
    search_request = client.search_all_iam_policies.call_args.kwargs["request"]
    assert (
        list(search_request.asset_types)
        == policy_bindings.GCP_POLICY_BINDINGS_SEARCH_ASSET_TYPES
    )
    assert "artifactregistry.googleapis.com/Repository" in search_request.asset_types
    assert (
        "artifactregistry.googleapis.com/DockerImage" not in search_request.asset_types
    )
    assert mock_wait_for_slot.call_count == 2


def test_split_bindings_by_graph_scope_keeps_inherited_separate():
    direct_project = {
        "id": "project-binding",
        "resource": "//cloudresourcemanager.googleapis.com/projects/project-abc",
        "resource_type": "project",
    }
    direct_resource = {
        "id": "bucket-binding",
        "resource": "//storage.googleapis.com/buckets/test-bucket",
        "resource_type": "resource",
    }
    inherited_org = {
        "id": "org-binding",
        "resource": "//cloudresourcemanager.googleapis.com/organizations/1337",
        "resource_type": "organization",
    }
    inherited_folder = {
        "id": "folder-binding",
        "resource": "//cloudresourcemanager.googleapis.com/folders/1414",
        "resource_type": "folder",
    }

    direct, inherited = policy_bindings._split_bindings_by_graph_scope(
        [direct_project, direct_resource, inherited_org, inherited_folder]
    )

    assert direct == [direct_project, direct_resource]
    assert inherited == {
        ("GCPOrganization", "organizations/1337"): [inherited_org],
        ("GCPFolder", "folders/1414"): [inherited_folder],
    }


def test_claim_inherited_bindings_for_graph_dedupes_per_claim_state():
    inherited = {
        ("GCPOrganization", "organizations/1337"): [
            {
                "id": "org-binding",
                "resource": "//cloudresourcemanager.googleapis.com/organizations/1337",
                "resource_type": "organization",
            },
        ],
    }
    claim_state = policy_bindings.InheritedPolicyBindingClaimState()

    first_claim = policy_bindings._claim_inherited_bindings_for_graph(
        inherited,
        claim_state,
    )
    second_claim = policy_bindings._claim_inherited_bindings_for_graph(
        inherited,
        claim_state,
    )
    next_run_claim = policy_bindings._claim_inherited_bindings_for_graph(
        inherited,
        policy_bindings.InheritedPolicyBindingClaimState(),
    )

    assert first_claim == inherited
    assert second_claim == {}
    assert next_run_claim == inherited


@patch.object(policy_bindings, "load_matchlinks")
@patch.object(policy_bindings, "load")
def test_load_bindings_uses_policy_binding_batch_size(mock_load, mock_load_matchlinks):
    bindings = [
        {
            "id": "binding-1",
            "resource": "//storage.googleapis.com/buckets/test-bucket",
        },
    ]

    policy_bindings.load_bindings(
        MagicMock(),
        bindings,
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
    )

    assert (
        mock_load.call_args.kwargs["batch_size"]
        == policy_bindings.GCP_POLICY_BINDINGS_GRAPH_BATCH_SIZE
    )
    assert (
        mock_load_matchlinks.call_args.kwargs["batch_size"]
        == policy_bindings.GCP_POLICY_BINDINGS_GRAPH_BATCH_SIZE
    )


@patch.object(policy_bindings, "load_matchlinks")
@patch.object(policy_bindings, "load")
def test_load_inherited_bindings_uses_owner_scope(mock_load, mock_load_matchlinks):
    inherited = {
        ("GCPOrganization", "organizations/1337"): [
            {
                "id": "org-binding",
                "resource": "//cloudresourcemanager.googleapis.com/organizations/1337",
                "resource_type": "organization",
            },
        ],
        ("GCPFolder", "folders/1414"): [
            {
                "id": "folder-binding",
                "resource": "//cloudresourcemanager.googleapis.com/folders/1414",
                "resource_type": "folder",
            },
        ],
    }

    loaded_count = policy_bindings.load_inherited_bindings(
        MagicMock(),
        inherited,
        TEST_UPDATE_TAG,
    )

    assert loaded_count == 2
    assert mock_load.call_count == 2
    assert mock_load.call_args_list[0].kwargs["ORG_RESOURCE_NAME"] == (
        "organizations/1337"
    )
    assert mock_load.call_args_list[1].kwargs["FOLDER_ID"] == "folders/1414"
    assert mock_load_matchlinks.call_count == 2
    assert mock_load_matchlinks.call_args_list[0].kwargs["_sub_resource_label"] == (
        "GCPOrganization"
    )
    assert mock_load_matchlinks.call_args_list[0].kwargs["_sub_resource_id"] == (
        "organizations/1337"
    )
    assert mock_load_matchlinks.call_args_list[1].kwargs["_sub_resource_label"] == (
        "GCPFolder"
    )
    assert mock_load_matchlinks.call_args_list[1].kwargs["_sub_resource_id"] == (
        "folders/1414"
    )


@patch.object(policy_bindings, "GraphStatement")
@patch("cartography.intel.gcp.policy_bindings.GraphJob.from_node_schema")
def test_cleanup_uses_one_generic_applies_to_cleanup(
    mock_from_node_schema,
    mock_graph_statement,
):
    neo4j_session = MagicMock()
    cleanup_job = MagicMock()
    mock_from_node_schema.return_value = cleanup_job
    applies_to_cleanup = MagicMock()
    mock_graph_statement.return_value = applies_to_cleanup

    policy_bindings.cleanup(neo4j_session, COMMON_JOB_PARAMS)

    assert (
        mock_from_node_schema.call_args.kwargs["iterationsize"]
        == policy_bindings.GCP_POLICY_BINDINGS_CLEANUP_ITERATION_SIZE
    )
    cleanup_job.run.assert_called_once_with(neo4j_session)
    mock_graph_statement.assert_called_once()
    query = mock_graph_statement.call_args.args[0]
    assert "MATCH (:GCPPolicyBinding)-[r:APPLIES_TO]->()" in query
    assert "r._sub_resource_id = $_sub_resource_id" in query
    assert (
        mock_graph_statement.call_args.kwargs["iterationsize"]
        == policy_bindings.GCP_POLICY_BINDINGS_CLEANUP_ITERATION_SIZE
    )
    applies_to_cleanup.run.assert_called_once_with(neo4j_session)


@patch.object(policy_bindings, "GraphStatement")
@patch("cartography.intel.gcp.policy_bindings.GraphJob.from_node_schema")
def test_cleanup_inherited_policy_bindings_cleans_org_and_folders(
    mock_from_node_schema,
    mock_graph_statement,
):
    neo4j_session = MagicMock()
    mock_from_node_schema.return_value = MagicMock()
    mock_graph_statement.return_value = MagicMock()

    policy_bindings.cleanup_inherited_policy_bindings(
        neo4j_session,
        COMMON_JOB_PARAMS,
        ["folders/1414"],
    )

    assert mock_from_node_schema.call_count == 2
    assert mock_graph_statement.call_count == 2
    assert (
        mock_graph_statement.call_args_list[0].kwargs["parameters"][
            "_sub_resource_label"
        ]
        == "GCPOrganization"
    )
    assert (
        mock_graph_statement.call_args_list[0].kwargs["parameters"]["_sub_resource_id"]
        == "organizations/1337"
    )
    assert (
        mock_graph_statement.call_args_list[1].kwargs["parameters"][
            "_sub_resource_label"
        ]
        == "GCPFolder"
    )
    assert (
        mock_graph_statement.call_args_list[1].kwargs["parameters"]["_sub_resource_id"]
        == "folders/1414"
    )


@patch.object(policy_bindings, "cleanup")
@patch.object(policy_bindings, "load_bindings")
@patch.object(policy_bindings, "load_inherited_bindings", return_value=1)
@patch.object(policy_bindings, "build_principals_from_policy_bindings")
@patch.object(policy_bindings, "transform_bindings")
@patch.object(policy_bindings, "get_policy_bindings")
def test_sync_limits_policy_binding_graph_writes(
    mock_get_policy_bindings,
    mock_transform_bindings,
    mock_build_principals,
    mock_load_inherited_bindings,
    mock_load_bindings,
    mock_cleanup,
):
    graph_semaphore = MagicMock()
    mock_get_policy_bindings.return_value = {"policy_results": []}
    mock_transform_bindings.return_value = [{"id": "binding-1"}]
    mock_build_principals.return_value = {}

    with patch.object(
        policy_bindings,
        "_GCP_POLICY_BINDINGS_GRAPH_SEMAPHORE",
        graph_semaphore,
    ):
        result = policy_bindings.sync(
            MagicMock(),
            TEST_PROJECT_ID,
            TEST_UPDATE_TAG,
            COMMON_JOB_PARAMS,
            MagicMock(),
            {},
        )

    assert result.status == policy_bindings.PolicyBindingsSyncStatus.SUCCESS
    graph_semaphore.__enter__.assert_called_once()
    graph_semaphore.__exit__.assert_called_once()
    mock_load_bindings.assert_called_once()
    mock_load_inherited_bindings.assert_called_once()
    mock_cleanup.assert_called_once()


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

    result = cartography.intel.gcp._sync_project_resources(
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
    assert result.policy_bindings_cleanup_safe is False


@patch("cartography.intel.gcp.build_asset_client")
@patch("cartography.intel.gcp.build_client")
@patch(
    "cartography.intel.gcp.policy_bindings.sync",
    side_effect=[
        policy_bindings.PolicyBindingsSyncResult(
            policy_bindings.PolicyBindingsSyncStatus.SUCCESS,
            {},
        ),
        policy_bindings.PolicyBindingsSyncResult(
            policy_bindings.PolicyBindingsSyncStatus.SKIPPED_RATE_LIMIT,
            {},
        ),
    ],
)
@patch(
    "cartography.intel.gcp._services_enabled_on_project",
    side_effect=[
        set(),
        {cartography.intel.gcp.service_names.cai},
        set(),
    ],
)
def test_sync_project_resources_reports_policy_bindings_partial_failure(
    mock_services_enabled,
    mock_policy_bindings_sync,
    mock_build_client,
    mock_build_asset_client,
):
    mock_build_client.return_value = MagicMock()
    mock_build_asset_client.return_value = MagicMock()

    result = cartography.intel.gcp._sync_project_resources(
        neo4j_session=MagicMock(),
        projects=[
            {"projectId": TEST_PROJECT_ID},
            {"projectId": "project-def"},
        ],
        gcp_update_tag=TEST_UPDATE_TAG,
        common_job_parameters=COMMON_JOB_PARAMS.copy(),
        credentials=MagicMock(),
        requested_syncs={"policy_bindings"},
    )

    assert mock_services_enabled.call_count == 3
    assert mock_policy_bindings_sync.call_count == 2
    assert result.policy_bindings_cleanup_safe is False


@patch("cartography.intel.gcp.build_asset_client")
@patch("cartography.intel.gcp.build_client")
@patch(
    "cartography.intel.gcp.policy_bindings.sync",
    return_value=policy_bindings.PolicyBindingsSyncResult(
        policy_bindings.PolicyBindingsSyncStatus.SUCCESS,
        {},
    ),
)
@patch(
    "cartography.intel.gcp._services_enabled_on_project",
    side_effect=[
        set(),
        {cartography.intel.gcp.service_names.cai},
        set(),
    ],
)
def test_sync_project_resources_reports_policy_bindings_full_success(
    mock_services_enabled,
    mock_policy_bindings_sync,
    mock_build_client,
    mock_build_asset_client,
):
    mock_build_client.return_value = MagicMock()
    mock_build_asset_client.return_value = MagicMock()

    result = cartography.intel.gcp._sync_project_resources(
        neo4j_session=MagicMock(),
        projects=[
            {"projectId": TEST_PROJECT_ID},
            {"projectId": "project-def"},
        ],
        gcp_update_tag=TEST_UPDATE_TAG,
        common_job_parameters=COMMON_JOB_PARAMS.copy(),
        credentials=MagicMock(),
        requested_syncs={"policy_bindings"},
    )

    assert mock_services_enabled.call_count == 3
    assert mock_policy_bindings_sync.call_count == 2
    assert result.policy_bindings_cleanup_safe is True


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

    result = cartography.intel.gcp._sync_project_resources(
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
    assert result.policy_bindings_cleanup_safe is False
