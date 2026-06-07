from types import SimpleNamespace
from unittest.mock import call
from unittest.mock import MagicMock
from unittest.mock import patch

from cartography.intel.gcp.crm.folders import get_default_apps_script_folder_names
from cartography.intel.gcp.crm.projects import get_gcp_projects


def test_get_default_apps_script_folder_names_only_matches_documented_lineage():
    folders = [
        {
            "name": "folders/business",
            "parent": "organizations/123456789012",
            "displayName": "business-unit",
            "lifecycleState": "ACTIVE",
        },
        {
            "name": "folders/system",
            "parent": "organizations/123456789012",
            "displayName": "system-gsuite",
            "lifecycleState": "ACTIVE",
        },
        {
            "name": "folders/default-apps-script",
            "parent": "folders/system",
            "displayName": "apps-script",
            "lifecycleState": "ACTIVE",
        },
        {
            "name": "folders/custom-apps-script",
            "parent": "folders/business",
            "displayName": "apps-script",
            "lifecycleState": "ACTIVE",
        },
    ]

    assert get_default_apps_script_folder_names(folders) == {
        "folders/default-apps-script",
    }


def test_get_default_apps_script_folder_names_requires_direct_system_parent():
    folders = [
        {
            "name": "folders/system",
            "parent": "organizations/123456789012",
            "displayName": "system-gsuite",
            "lifecycleState": "ACTIVE",
        },
        {
            "name": "folders/intermediate",
            "parent": "folders/system",
            "displayName": "intermediate",
            "lifecycleState": "ACTIVE",
        },
        {
            "name": "folders/nested-apps-script",
            "parent": "folders/intermediate",
            "displayName": "apps-script",
            "lifecycleState": "ACTIVE",
        },
    ]

    assert get_default_apps_script_folder_names(folders) == set()


def test_get_gcp_projects_skips_default_apps_script_parent_only():
    folders = [
        {
            "name": "folders/business",
            "parent": "organizations/123456789012",
            "displayName": "business-unit",
            "lifecycleState": "ACTIVE",
        },
        {
            "name": "folders/system",
            "parent": "organizations/123456789012",
            "displayName": "system-gsuite",
            "lifecycleState": "ACTIVE",
        },
        {
            "name": "folders/default-apps-script",
            "parent": "folders/system",
            "displayName": "apps-script",
            "lifecycleState": "ACTIVE",
        },
        {
            "name": "folders/engineering",
            "parent": "folders/business",
            "displayName": "engineering",
            "lifecycleState": "ACTIVE",
        },
    ]
    mock_client = MagicMock()
    projects_by_parent = {
        "organizations/123456789012": [
            SimpleNamespace(
                name="projects/1001",
                project_id="org-root-project",
                display_name="Org Root Project",
                state=SimpleNamespace(name="ACTIVE"),
                parent="organizations/123456789012",
            ),
        ],
        "folders/business": [
            SimpleNamespace(
                name="projects/1002",
                project_id="business-project",
                display_name="Business Project",
                state=SimpleNamespace(name="ACTIVE"),
                parent="folders/business",
            ),
        ],
        "folders/engineering": [
            SimpleNamespace(
                name="projects/1003",
                project_id="standard-apps-script-project",
                display_name="Standard Apps Script Project",
                state=SimpleNamespace(name="ACTIVE"),
                parent="folders/engineering",
            ),
        ],
        "folders/system": [],
    }
    mock_client.list_projects.side_effect = lambda *, parent: projects_by_parent[parent]

    with patch(
        "cartography.intel.gcp.crm.projects.resourcemanager_v3.ProjectsClient",
        return_value=mock_client,
    ):
        projects = get_gcp_projects("organizations/123456789012", folders)

    assert {
        listed_parent.kwargs["parent"]
        for listed_parent in mock_client.list_projects.call_args_list
    } == {
        "organizations/123456789012",
        "folders/business",
        "folders/engineering",
        "folders/system",
    }
    assert (
        call(parent="folders/default-apps-script")
        not in mock_client.list_projects.call_args_list
    )
    assert {project["projectId"] for project in projects} == {
        "org-root-project",
        "business-project",
        "standard-apps-script-project",
    }
