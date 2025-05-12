from unittest.mock import patch

import cartography.intel.digitalocean.platform
import tests.data.digitalocean.platform
from tests.integration.util import check_nodes

TEST_UPDATE_TAG = 123456789


def _ensure_local_neo4j_has_account_data(neo4j_session):
    data = cartography.intel.digitalocean.platform.transform_account(
        tests.data.digitalocean.platform.ACCOUNT_RESPONSE
    )
    cartography.intel.digitalocean.platform.load_account(
        neo4j_session, [data], TEST_UPDATE_TAG
    )


@patch.object(
    cartography.intel.digitalocean.platform,
    "get_account",
    return_value=tests.data.digitalocean.platform.ACCOUNT_RESPONSE,
)
@patch("digitalocean.Manager")
def test_transform_and_load_account(mock_do_manager, mock_api, neo4j_session):
    cartography.intel.digitalocean.platform.sync(
        neo4j_session,
        mock_do_manager,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )

    account_res = tests.data.digitalocean.platform.ACCOUNT_RESPONSE
    assert check_nodes(
        neo4j_session,
        "DOAccount",
        ["id", "uuid", "droplet_limit", "floating_ip_limit", "status"],
    ) == {
        (
            account_res.uuid,
            account_res.uuid,
            account_res.droplet_limit,
            account_res.floating_ip_limit,
            account_res.status,
        ),
    }
