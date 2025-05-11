from unittest.mock import patch

import cartography.intel.digitalocean.compute
import tests.data.digitalocean.compute
from tests.integration.cartography.intel.digitalocean.test_management import (
    _ensure_local_neo4j_has_project_data,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


@patch.object(
    cartography.intel.digitalocean.compute,
    "get_droplets",
    return_value=tests.data.digitalocean.compute.DROPLETS_RESPONSE,
)
@patch("digitalocean.Manager")
def test_transform_and_load_droplets(mock_do_manager, mock_api, neo4j_session):
    droplet_res = tests.data.digitalocean.compute.DROPLETS_RESPONSE
    test_droplet = droplet_res[0]
    account_id = "123-4567-8789"
    project_id = "project_1"

    _ensure_local_neo4j_has_project_data(neo4j_session)

    cartography.intel.digitalocean.compute.sync(
        neo4j_session,
        mock_do_manager,
        account_id,
        {
            str(project_id): [
                "do:droplet:" + test_droplet.id,
            ],
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
        (test_droplet.id, test_droplet.name, test_droplet.ip_address),
    }
    # Check the projects relationships
    assert check_rels(
        neo4j_session,
        "DODroplet",
        "id",
        "DOProject",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (
            test_droplet.id,
            project_id,
        ),
    }
