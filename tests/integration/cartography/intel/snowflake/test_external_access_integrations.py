from unittest.mock import patch

import cartography.intel.snowflake.external_access_integrations
from tests.data.snowflake.account import SNOWFLAKE_ACCOUNT_ID
from tests.data.snowflake.external_access_integrations import (
    SNOWFLAKE_EXTERNAL_ACCESS_INTEGRATIONS,
)
from tests.integration.cartography.intel.snowflake.test_account import build_test_client
from tests.integration.cartography.intel.snowflake.test_account import TEST_UPDATE_TAG
from tests.integration.cartography.intel.snowflake.test_network_rules import (
    _ensure_local_neo4j_has_test_network_rules,
)
from tests.integration.cartography.intel.snowflake.test_network_rules import (
    DUFF_API_EGRESS_ID,
)
from tests.integration.cartography.intel.snowflake.test_secrets import (
    _ensure_local_neo4j_has_test_secrets,
)
from tests.integration.cartography.intel.snowflake.test_secrets import DUFF_API_TOKEN_ID
from tests.integration.cartography.intel.snowflake.test_security_integrations import (
    _ensure_local_neo4j_has_test_security_integrations,
)
from tests.integration.cartography.intel.snowflake.test_security_integrations import (
    DUFF_OAUTH_ID,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

DUFF_API_ACCESS_ID = "SPRINGFIELD.NUCLEAR/external_access_integration/DUFF_API_ACCESS"
MOE_TAB_ACCESS_ID = "SPRINGFIELD.NUCLEAR/external_access_integration/MOE_TAB_ACCESS"


def _ensure_local_neo4j_has_test_external_access_integrations(neo4j_session) -> None:
    """Seed the external access integrations a service's USES_INTEGRATION edge needs."""
    cartography.intel.snowflake.external_access_integrations.load_external_access_integrations(
        neo4j_session,
        cartography.intel.snowflake.external_access_integrations.transform(
            SNOWFLAKE_EXTERNAL_ACCESS_INTEGRATIONS, SNOWFLAKE_ACCOUNT_ID
        ),
        SNOWFLAKE_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.snowflake.external_access_integrations,
    "get",
    return_value=SNOWFLAKE_EXTERNAL_ACCESS_INTEGRATIONS,
)
def test_sync_snowflake_external_access_integrations(mock_get, neo4j_session):
    # Arrange: every allow-list entry names an object another sync owns.
    _ensure_local_neo4j_has_test_network_rules(neo4j_session)
    _ensure_local_neo4j_has_test_secrets(neo4j_session)
    _ensure_local_neo4j_has_test_security_integrations(neo4j_session)

    # Act
    complete = cartography.intel.snowflake.external_access_integrations.sync(
        neo4j_session,
        build_test_client(),
        {"UPDATE_TAG": TEST_UPDATE_TAG, "ACCOUNT_ID": SNOWFLAKE_ACCOUNT_ID},
    )

    # Assert
    assert complete is True
    assert check_nodes(
        neo4j_session,
        "SnowflakeExternalAccessIntegration",
        ["id", "name", "enabled"],
    ) == {
        (DUFF_API_ACCESS_ID, "DUFF_API_ACCESS", True),
        (MOE_TAB_ACCESS_ID, "MOE_TAB_ACCESS", False),
    }
    assert check_rels(
        neo4j_session,
        "SnowflakeExternalAccessIntegration",
        "id",
        "SnowflakeAccount",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        (DUFF_API_ACCESS_ID, SNOWFLAKE_ACCOUNT_ID),
        (MOE_TAB_ACCESS_ID, SNOWFLAKE_ACCOUNT_ID),
    }
    # The bracketed SHOW strings are resolved back into real edges, which is what makes
    # "which code can reach the internet, and with which credential" answerable. The
    # integration that allows nothing gets no edges.
    assert check_rels(
        neo4j_session,
        "SnowflakeExternalAccessIntegration",
        "id",
        "SnowflakeNetworkRule",
        "id",
        "ALLOWS",
        rel_direction_right=True,
    ) == {(DUFF_API_ACCESS_ID, DUFF_API_EGRESS_ID)}
    assert check_rels(
        neo4j_session,
        "SnowflakeExternalAccessIntegration",
        "id",
        "SnowflakeSecret",
        "id",
        "ALLOWS_SECRET",
        rel_direction_right=True,
    ) == {(DUFF_API_ACCESS_ID, DUFF_API_TOKEN_ID)}
    assert check_rels(
        neo4j_session,
        "SnowflakeExternalAccessIntegration",
        "id",
        "SnowflakeSecurityIntegration",
        "id",
        "ALLOWS_AUTH_INTEGRATION",
        rel_direction_right=True,
    ) == {(DUFF_API_ACCESS_ID, DUFF_OAUTH_ID)}
