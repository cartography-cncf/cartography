from unittest.mock import MagicMock

import cartography.intel.digitalocean.management
import tests.data.digitalocean.management
import tests.data.digitalocean.platform
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


def _ensure_local_neo4j_has_account_data(neo4j_session):
    data = cartography.intel.digitalocean.platform.transform_account(
        tests.data.digitalocean.platform.ACCOUNT_RESPONSE.get("account", {})
    )
    cartography.intel.digitalocean.platform.load_account(
        neo4j_session, [data], TEST_UPDATE_TAG
    )


def test_transform_and_load_projects(neo4j_session):
    _ensure_local_neo4j_has_account_data(neo4j_session)

    projects_res = tests.data.digitalocean.management.PROJECTS_RESPONSE
    test_project = projects_res.get("projects", [])[0]
    account_id = "test-account-uuid"

    mock_client = MagicMock()
    mock_client.projects.list.return_value = (
        tests.data.digitalocean.management.PROJECTS_RESPONSE
    )
    mock_client.projects.list_resources.return_value = (
        tests.data.digitalocean.management.PROJECT_RESOURCES_RESPONSE
    )

    cartography.intel.digitalocean.management.sync(
        neo4j_session,
        mock_client,
        account_id,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "ACCOUNT_ID": account_id},
    )

    # Check the projects nodes
    assert check_nodes(
        neo4j_session,
        "DOProject",
        ["id", "name", "owner_uuid"],
    ) == {
        (
            test_project.get("id"),
            test_project.get("name"),
            test_project.get("owner_uuid"),
        ),
    }

    # Check the projects relationships
    assert check_rels(
        neo4j_session,
        "DOProject",
        "id",
        "DOAccount",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        (
            test_project.get("id"),
            account_id,
        ),
    }


def test_transform_and_load_projects_paginated(neo4j_session):
    _ensure_local_neo4j_has_account_data(neo4j_session)

    projects_res = tests.data.digitalocean.management.PROJECTS_RESPONSE_PAGINATED
    test_project1 = projects_res[0].get("projects", [])[0]
    test_project2 = projects_res[1].get("projects", [])[0]
    account_id = "test-account-uuid"

    mock_client = MagicMock()
    mock_client.projects.list.side_effect = (
        tests.data.digitalocean.management.PROJECTS_RESPONSE_PAGINATED
    )

    mock_client.projects.list_resources.return_value = (
        tests.data.digitalocean.management.PROJECT_RESOURCES_RESPONSE
    )

    cartography.intel.digitalocean.management.sync(
        neo4j_session,
        mock_client,
        account_id,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "ACCOUNT_ID": account_id},
    )

    # Check the projects nodes
    assert check_nodes(
        neo4j_session,
        "DOProject",
        ["id", "name", "owner_uuid"],
    ) == {
        (
            test_project1.get("id"),
            test_project1.get("name"),
            test_project1.get("owner_uuid"),
        ),
        (
            test_project2.get("id"),
            test_project2.get("name"),
            test_project2.get("owner_uuid"),
        ),
    }

    # Check the projects relationships
    assert check_rels(
        neo4j_session,
        "DOProject",
        "id",
        "DOAccount",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        (
            test_project1.get("id"),
            account_id,
        ),
        (
            test_project2.get("id"),
            account_id,
        ),
    }
