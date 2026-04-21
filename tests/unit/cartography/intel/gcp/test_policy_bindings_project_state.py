from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.gcp


def _make_configured_projects():
    return [
        {"projectId": "project-without-cai"},
        {"projectId": "project-with-cai"},
    ]


@patch.object(cartography.intel.gcp.policy_bindings, "sync", return_value=False)
@patch.object(cartography.intel.gcp, "build_asset_client", return_value=MagicMock())
@patch.object(cartography.intel.gcp, "_services_enabled_on_project")
@patch.object(cartography.intel.gcp, "_get_cached_client")
def test_policy_bindings_evaluates_cai_per_project(
    mock_get_cached_client,
    mock_services_enabled_on_project,
    _mock_build_asset_client,
    mock_policy_bindings_sync,
):
    mock_get_cached_client.return_value = MagicMock()
    mock_services_enabled_on_project.side_effect = [
        set(),
        {cartography.intel.gcp.service_names.cai},
    ]

    cartography.intel.gcp._sync_project_resources(
        neo4j_session=MagicMock(),
        projects=_make_configured_projects(),
        gcp_update_tag=123,
        common_job_parameters={
            "UPDATE_TAG": 123,
            "ORG_RESOURCE_NAME": "organizations/1",
        },
        credentials=MagicMock(),
        client_cache={},
        requested_syncs={"policy_bindings"},
    )

    mock_policy_bindings_sync.assert_called_once()
    assert mock_policy_bindings_sync.call_args.args[1] == "project-with-cai"


@patch.object(cartography.intel.gcp.policy_bindings, "sync", side_effect=[False, True])
@patch.object(cartography.intel.gcp, "build_asset_client", return_value=MagicMock())
@patch.object(cartography.intel.gcp, "_services_enabled_on_project")
@patch.object(cartography.intel.gcp, "_get_cached_client")
def test_policy_bindings_permission_denied_does_not_skip_later_projects(
    mock_get_cached_client,
    mock_services_enabled_on_project,
    _mock_build_asset_client,
    mock_policy_bindings_sync,
):
    mock_get_cached_client.return_value = MagicMock()
    mock_services_enabled_on_project.side_effect = [
        {cartography.intel.gcp.service_names.cai},
        {cartography.intel.gcp.service_names.cai},
    ]

    cartography.intel.gcp._sync_project_resources(
        neo4j_session=MagicMock(),
        projects=[
            {"projectId": "project-denied"},
            {"projectId": "project-allowed"},
        ],
        gcp_update_tag=123,
        common_job_parameters={
            "UPDATE_TAG": 123,
            "ORG_RESOURCE_NAME": "organizations/1",
        },
        credentials=MagicMock(),
        client_cache={},
        requested_syncs={"policy_bindings"},
    )

    assert mock_policy_bindings_sync.call_count == 2
    assert [call.args[1] for call in mock_policy_bindings_sync.call_args_list] == [
        "project-denied",
        "project-allowed",
    ]
