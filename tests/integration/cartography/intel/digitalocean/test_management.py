from unittest.mock import patch

import digitalocean

import cartography.intel.digitalocean.management
import tests.data.digitalocean.management
from tests.integration.cartography.intel.digitalocean.test_platform import (
    _ensure_local_neo4j_has_account_data,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


def _ensure_local_neo4j_has_project_data(neo4j_session):
    data = cartography.intel.digitalocean.management.transform_projects(
        tests.data.digitalocean.management.PROJECTS_RESPONSE
    )
    cartography.intel.digitalocean.management.load_projects(
        neo4j_session, data, "123-4567-8789", TEST_UPDATE_TAG
    )


@patch.object(
    cartography.intel.digitalocean.management,
    "get_projects",
    return_value=tests.data.digitalocean.management.PROJECTS_RESPONSE,
)
@patch.object(
    digitalocean.Project,
    "get_all_resources",
    return_value=tests.data.digitalocean.management.PROJECT_RESOURCES_RESPONSE,
)
@patch("digitalocean.Manager")
def test_transform_and_load_projects(
    mock_do_manager, mock_do_project, mock_api, neo4j_session
):
    _ensure_local_neo4j_has_account_data(neo4j_session)

    projects_res = tests.data.digitalocean.management.PROJECTS_RESPONSE
    test_project = projects_res[0]
    account_id = "123-4567-8789"

    cartography.intel.digitalocean.management.sync(
        neo4j_session,
        mock_do_manager,
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
            test_project.id,
            test_project.name,
            test_project.owner_uuid,
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
        rel_direction_right=True,
    ) == {
        (
            test_project.id,
            account_id,
        ),
    }
