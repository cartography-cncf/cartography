from unittest.mock import MagicMock

import cartography.intel.digitalocean.compute
import tests.data.digitalocean.compute
import tests.data.digitalocean.management
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


def _ensure_local_neo4j_has_project_data(neo4j_session):
    data = cartography.intel.digitalocean.management.transform_projects(
        tests.data.digitalocean.management.PROJECTS_RESPONSE.get("projects", [])
    )
    cartography.intel.digitalocean.management.load_projects(
        neo4j_session, data, "123-4567-8789", TEST_UPDATE_TAG
    )


def test_transform_and_load_droplets(neo4j_session):
    droplet_res = tests.data.digitalocean.compute.DROPLETS_RESPONSE.get("droplets", [])
    test_droplet = droplet_res[0]
    account_id = "test-account-uuid"
    project_id = "test-project-uuid"

    mock_client = MagicMock()
    mock_client.droplets.list.return_value = (
        tests.data.digitalocean.compute.DROPLETS_RESPONSE
    )

    _ensure_local_neo4j_has_project_data(neo4j_session)

    cartography.intel.digitalocean.compute.sync(
        neo4j_session,
        mock_client,
        account_id,
        {
            str(project_id): [
                {
                    "urn": f"do:droplet:{test_droplet.get('id', '')}",
                }
            ]
        },
        TEST_UPDATE_TAG,
        {
            "UPDATE_TAG": TEST_UPDATE_TAG,
            "ACCOUNT_ID": account_id,
        },
    )

    # Check the droplets nodes
    assert check_nodes(
        neo4j_session,
        "DODroplet",
        [
            "id",
            "name",
            "ip_address",
        ],
    ) == {
        (
            test_droplet.get("id", ""),
            test_droplet.get("name", ""),
            "111.222.333.444",
        ),
    }
    # Check the projects relationships
    assert check_rels(
        neo4j_session,
        "DODroplet",
        "id",
        "DOProject",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        (
            test_droplet.get("id", 0),
            project_id,
        ),
    }
