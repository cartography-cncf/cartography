from unittest.mock import MagicMock

import cartography.intel.digitalocean.platform
import tests.data.digitalocean.platform
from tests.integration.util import check_nodes

TEST_UPDATE_TAG = 123456789


def test_transform_and_load_account(neo4j_session):

    mock_client = MagicMock()
    mock_client.account.get.return_value = (
        tests.data.digitalocean.platform.ACCOUNT_RESPONSE
    )

    cartography.intel.digitalocean.platform.sync(
        neo4j_session,
        mock_client,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )

    account_res = tests.data.digitalocean.platform.ACCOUNT_RESPONSE.get("account", {})
    assert check_nodes(
        neo4j_session,
        "DOAccount",
        ["id", "uuid", "droplet_limit", "floating_ip_limit", "status"],
    ) == {
        (
            account_res.get("uuid", ""),
            account_res.get("uuid", ""),
            account_res.get("droplet_limit", 0),
            account_res.get("floating_ip_limit", 0),
            account_res.get("status", ""),
        ),
    }
