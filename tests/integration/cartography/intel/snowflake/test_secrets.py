from unittest.mock import patch

import cartography.intel.snowflake.secrets
from tests.data.snowflake.account import SNOWFLAKE_ACCOUNT_ID
from tests.data.snowflake.secrets import SNOWFLAKE_SECRETS
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
from tests.integration.cartography.intel.snowflake.test_security_integrations import (
    _ensure_local_neo4j_has_test_security_integrations,
)
from tests.integration.cartography.intel.snowflake.test_security_integrations import (
    DUFF_OAUTH_ID,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

DUFF_API_TOKEN_ID = (
    "SPRINGFIELD.NUCLEAR/secret/SPRINGFIELD.NUCLEAR_PLANT.DUFF_API_TOKEN"
)
MOE_TAB_LOGIN_ID = "SPRINGFIELD.NUCLEAR/secret/SPRINGFIELD.NUCLEAR_PLANT.MOE_TAB_LOGIN"
SQUISHEE_HMAC_KEY_ID = (
    "SPRINGFIELD.NUCLEAR/secret/SPRINGFIELD.KWIK_E_MART.SQUISHEE_HMAC_KEY"
)


def _ensure_local_neo4j_has_test_secrets(neo4j_session) -> None:
    """Seed the secrets an external access integration's ALLOWS_SECRET edge resolves against."""
    _ensure_local_neo4j_has_test_schemas(neo4j_session)
    cartography.intel.snowflake.secrets.load_secrets(
        neo4j_session,
        cartography.intel.snowflake.secrets.transform(
            SNOWFLAKE_SECRETS, SNOWFLAKE_ACCOUNT_ID
        ),
        SNOWFLAKE_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.snowflake.secrets,
    "get",
    return_value=(SNOWFLAKE_SECRETS, True),
)
def test_sync_snowflake_secrets(mock_get, neo4j_session):
    # Arrange
    _ensure_local_neo4j_has_test_schemas(neo4j_session)
    _ensure_local_neo4j_has_test_security_integrations(neo4j_session)

    # Act
    complete = cartography.intel.snowflake.secrets.sync(
        neo4j_session,
        build_test_client(),
        TEST_SCHEMAS,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "ACCOUNT_ID": SNOWFLAKE_ACCOUNT_ID},
    )

    # Assert: the kind is read whichever field name the API version used, and the
    # username of a password secret is recorded while the password never is.
    assert complete is True
    assert check_nodes(
        neo4j_session,
        "SnowflakeSecret",
        ["id", "name", "secret_type", "username", "algorithm", "key_length"],
    ) == {
        (DUFF_API_TOKEN_ID, "DUFF_API_TOKEN", "OAUTH2", None, None, None),
        (MOE_TAB_LOGIN_ID, "MOE_TAB_LOGIN", "PASSWORD", "homer", None, None),
        (SQUISHEE_HMAC_KEY_ID, "SQUISHEE_HMAC_KEY", "SYMMETRIC_KEY", None, "AES", 256),
    }
    assert check_nodes(neo4j_session, "Secret", ["id"]) >= {
        (DUFF_API_TOKEN_ID,),
        (MOE_TAB_LOGIN_ID,),
        (SQUISHEE_HMAC_KEY_ID,),
    }
    assert check_rels(
        neo4j_session,
        "SnowflakeSecret",
        "id",
        "SnowflakeSchema",
        "id",
        "CONTAINS",
        rel_direction_right=False,
    ) == {
        (DUFF_API_TOKEN_ID, NUCLEAR_PLANT_SCHEMA_ID),
        (MOE_TAB_LOGIN_ID, NUCLEAR_PLANT_SCHEMA_ID),
        (SQUISHEE_HMAC_KEY_ID, KWIK_E_MART_SCHEMA_ID),
    }
    # Only the OAuth secret names an authentication integration, so only it gets the
    # edge to the identity provider that mints its token.
    assert check_rels(
        neo4j_session,
        "SnowflakeSecret",
        "id",
        "SnowflakeSecurityIntegration",
        "id",
        "USES_INTEGRATION",
        rel_direction_right=True,
    ) == {(DUFF_API_TOKEN_ID, DUFF_OAUTH_ID)}
