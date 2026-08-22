from unittest.mock import patch

import cartography.intel.snowflake.network_rules
from tests.data.snowflake.account import SNOWFLAKE_ACCOUNT_ID
from tests.data.snowflake.network_rules import SNOWFLAKE_NETWORK_RULES
from tests.integration.cartography.intel.snowflake.test_account import build_test_client
from tests.integration.cartography.intel.snowflake.test_account import TEST_UPDATE_TAG
from tests.integration.cartography.intel.snowflake.test_schemas import (
    _ensure_local_neo4j_has_test_schemas,
)
from tests.integration.cartography.intel.snowflake.test_schemas import (
    KWIK_E_MART_SCHEMA_ID,
)
from tests.integration.cartography.intel.snowflake.test_schemas import (
    NUCLEAR_PLANT_SCHEMA_ID,
)
from tests.integration.cartography.intel.snowflake.test_schemas import TEST_SCHEMAS
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

PLANT_OFFICE_IPS_ID = (
    "SPRINGFIELD.NUCLEAR/network_rule/SPRINGFIELD.NUCLEAR_PLANT.PLANT_OFFICE_IPS"
)
DUFF_API_EGRESS_ID = (
    "SPRINGFIELD.NUCLEAR/network_rule/SPRINGFIELD.NUCLEAR_PLANT.DUFF_API_EGRESS"
)
SQUISHEE_VPCE_ID = (
    "SPRINGFIELD.NUCLEAR/network_rule/SPRINGFIELD.KWIK_E_MART.SQUISHEE_VPCE"
)


def _ensure_local_neo4j_has_test_network_rules(neo4j_session) -> None:
    """Seed the network rules policies and external access integrations point at."""
    _ensure_local_neo4j_has_test_schemas(neo4j_session)
    cartography.intel.snowflake.network_rules.load_network_rules(
        neo4j_session,
        cartography.intel.snowflake.network_rules.transform(
            SNOWFLAKE_NETWORK_RULES, SNOWFLAKE_ACCOUNT_ID
        ),
        SNOWFLAKE_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.snowflake.network_rules,
    "get",
    return_value=(SNOWFLAKE_NETWORK_RULES, True),
)
def test_sync_snowflake_network_rules(mock_get, neo4j_session):
    # Arrange
    _ensure_local_neo4j_has_test_schemas(neo4j_session)

    # Act
    rules, complete = cartography.intel.snowflake.network_rules.sync(
        neo4j_session,
        build_test_client(),
        TEST_SCHEMAS,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "ACCOUNT_ID": SNOWFLAKE_ACCOUNT_ID},
    )

    # Assert: the mode is what separates an inbound allow-list from the egress rules an
    # external access integration can hand to handler code.
    assert complete is True
    assert check_nodes(
        neo4j_session,
        "SnowflakeNetworkRule",
        ["id", "name", "rule_type", "mode", "value_count"],
    ) == {
        (PLANT_OFFICE_IPS_ID, "PLANT_OFFICE_IPS", "IPV4", "INGRESS", 2),
        (DUFF_API_EGRESS_ID, "DUFF_API_EGRESS", "HOST_PORT", "EGRESS", 1),
        (SQUISHEE_VPCE_ID, "SQUISHEE_VPCE", "AWSVPCEID", "INGRESS", 1),
    }
    assert check_nodes(neo4j_session, "NetworkAccessControl", ["id"]) >= {
        (PLANT_OFFICE_IPS_ID,),
        (DUFF_API_EGRESS_ID,),
        (SQUISHEE_VPCE_ID,),
    }
    assert check_rels(
        neo4j_session,
        "SnowflakeNetworkRule",
        "id",
        "SnowflakeAccount",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        (PLANT_OFFICE_IPS_ID, SNOWFLAKE_ACCOUNT_ID),
        (DUFF_API_EGRESS_ID, SNOWFLAKE_ACCOUNT_ID),
        (SQUISHEE_VPCE_ID, SNOWFLAKE_ACCOUNT_ID),
    }
    assert check_rels(
        neo4j_session,
        "SnowflakeNetworkRule",
        "id",
        "SnowflakeSchema",
        "id",
        "CONTAINS",
        rel_direction_right=False,
    ) == {
        (PLANT_OFFICE_IPS_ID, NUCLEAR_PLANT_SCHEMA_ID),
        (DUFF_API_EGRESS_ID, NUCLEAR_PLANT_SCHEMA_ID),
        (SQUISHEE_VPCE_ID, KWIK_E_MART_SCHEMA_ID),
    }
