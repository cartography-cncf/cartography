from unittest.mock import patch

import cartography.intel.snowflake.functions
from tests.data.snowflake.account import SNOWFLAKE_ACCOUNT_ID
from tests.data.snowflake.functions import SNOWFLAKE_FUNCTIONS
from tests.integration.cartography.intel.snowflake.test_account import (
    _ensure_local_neo4j_has_test_account,
)
from tests.integration.cartography.intel.snowflake.test_account import build_test_client
from tests.integration.cartography.intel.snowflake.test_account import TEST_UPDATE_TAG
from tests.integration.cartography.intel.snowflake.test_tasks import (
    seed_schema_level_dependencies,
)
from tests.integration.cartography.intel.snowflake.test_tasks import TEST_SCHEMA_NAME
from tests.integration.cartography.intel.snowflake.test_tasks import TEST_SCHEMAS
from tests.integration.util import check_nodes
from tests.integration.util import check_rels


@patch.object(
    cartography.intel.snowflake.functions, "get", return_value=SNOWFLAKE_FUNCTIONS
)
def test_sync_snowflake_functions(mock_get, neo4j_session):
    # Arrange
    client = build_test_client()
    _ensure_local_neo4j_has_test_account(neo4j_session)
    seed_schema_level_dependencies(neo4j_session)
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ACCOUNT_ID": SNOWFLAKE_ACCOUNT_ID,
    }

    # Act
    complete = cartography.intel.snowflake.functions.sync(
        neo4j_session, client, TEST_SCHEMAS, common_job_parameters
    )

    # Assert: the two COOLANT_TEMP overloads stay separate nodes because the
    # argument list is part of the qualified name.
    assert complete is True
    assert check_nodes(neo4j_session, "SnowflakeFunction", ["qualified_name"]) == {
        ("SPRINGFIELD.NUCLEAR_PLANT.COOLANT_TEMP(NUMBER(38,0))",),
        ("SPRINGFIELD.NUCLEAR_PLANT.COOLANT_TEMP(NUMBER(38,0),VARCHAR)",),
        ("SPRINGFIELD.NUCLEAR_PLANT.DUFF_LOOKUP(VARCHAR)",),
    }

    # A function is a cross-provider Function and a grantable Snowflake object.
    assert check_nodes(neo4j_session, "Function", ["name"]) == {
        ("COOLANT_TEMP",),
        ("DUFF_LOOKUP",),
    }
    assert check_nodes(neo4j_session, "SnowflakeSecurable", ["name"]) >= {
        ("DUFF_LOOKUP",),
    }

    assert check_rels(
        neo4j_session,
        "SnowflakeAccount",
        "id",
        "SnowflakeFunction",
        "qualified_name",
        "RESOURCE",
    ) == {
        (SNOWFLAKE_ACCOUNT_ID, "SPRINGFIELD.NUCLEAR_PLANT.COOLANT_TEMP(NUMBER(38,0))"),
        (
            SNOWFLAKE_ACCOUNT_ID,
            "SPRINGFIELD.NUCLEAR_PLANT.COOLANT_TEMP(NUMBER(38,0),VARCHAR)",
        ),
        (SNOWFLAKE_ACCOUNT_ID, "SPRINGFIELD.NUCLEAR_PLANT.DUFF_LOOKUP(VARCHAR)"),
    }

    assert check_rels(
        neo4j_session,
        "SnowflakeSchema",
        "name",
        "SnowflakeFunction",
        "qualified_name",
        "CONTAINS",
    ) == {
        (TEST_SCHEMA_NAME, "SPRINGFIELD.NUCLEAR_PLANT.COOLANT_TEMP(NUMBER(38,0))"),
        (
            TEST_SCHEMA_NAME,
            "SPRINGFIELD.NUCLEAR_PLANT.COOLANT_TEMP(NUMBER(38,0),VARCHAR)",
        ),
        (TEST_SCHEMA_NAME, "SPRINGFIELD.NUCLEAR_PLANT.DUFF_LOOKUP(VARCHAR)"),
    }

    # Only the external function reaches out of Snowflake.
    assert check_rels(
        neo4j_session,
        "SnowflakeFunction",
        "name",
        "SnowflakeApiIntegration",
        "name",
        "USES_INTEGRATION",
    ) == {("DUFF_LOOKUP", "DUFF_API")}

    assert check_rels(
        neo4j_session,
        "SnowflakeFunction",
        "name",
        "SnowflakeExternalAccessIntegration",
        "name",
        "USES_INTEGRATION",
    ) == {("DUFF_LOOKUP", "DUFF_EAI")}

    # The mandated ontology edge name for a Function reading a Secret.
    assert check_rels(
        neo4j_session,
        "SnowflakeFunction",
        "name",
        "SnowflakeSecret",
        "name",
        "USES_SECRET",
    ) == {("DUFF_LOOKUP", "DUFF_TOKEN")}
