from unittest.mock import patch

import cartography.intel.snowflake.procedures
from tests.data.snowflake.account import SNOWFLAKE_ACCOUNT_ID
from tests.data.snowflake.procedures import SNOWFLAKE_PROCEDURES
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
    cartography.intel.snowflake.procedures, "get", return_value=SNOWFLAKE_PROCEDURES
)
def test_sync_snowflake_procedures(mock_get, neo4j_session):
    # Arrange
    client = build_test_client()
    _ensure_local_neo4j_has_test_account(neo4j_session)
    seed_schema_level_dependencies(neo4j_session)
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ACCOUNT_ID": SNOWFLAKE_ACCOUNT_ID,
    }

    # Act
    complete = cartography.intel.snowflake.procedures.sync(
        neo4j_session, client, TEST_SCHEMAS, common_job_parameters
    )

    # Assert
    assert complete is True
    assert check_nodes(
        neo4j_session, "SnowflakeProcedure", ["qualified_name", "execute_as"]
    ) == {
        ("SPRINGFIELD.NUCLEAR_PLANT.SCRAM_REACTOR(VARCHAR)", "OWNER"),
        ("SPRINGFIELD.NUCLEAR_PLANT.STIR_THE_POT()", "CALLER"),
    }

    assert check_nodes(neo4j_session, "Function", ["name"]) == {
        ("SCRAM_REACTOR",),
        ("STIR_THE_POT",),
    }

    assert check_rels(
        neo4j_session,
        "SnowflakeAccount",
        "id",
        "SnowflakeProcedure",
        "name",
        "RESOURCE",
    ) == {
        (SNOWFLAKE_ACCOUNT_ID, "SCRAM_REACTOR"),
        (SNOWFLAKE_ACCOUNT_ID, "STIR_THE_POT"),
    }

    assert check_rels(
        neo4j_session,
        "SnowflakeSchema",
        "name",
        "SnowflakeProcedure",
        "name",
        "CONTAINS",
    ) == {
        (TEST_SCHEMA_NAME, "SCRAM_REACTOR"),
        (TEST_SCHEMA_NAME, "STIR_THE_POT"),
    }

    # The escalation edge: only the owner-rights procedure lends its owner's
    # privileges to its callers. This is the mandated ontology edge name for a
    # Function reaching a PermissionRole.
    assert check_rels(
        neo4j_session,
        "SnowflakeProcedure",
        "name",
        "SnowflakeRole",
        "name",
        "ASSUMES",
    ) == {("SCRAM_REACTOR", "PLANT_ENGINEER")}

    assert check_rels(
        neo4j_session,
        "SnowflakeProcedure",
        "name",
        "SnowflakeExternalAccessIntegration",
        "name",
        "USES_INTEGRATION",
    ) == {("SCRAM_REACTOR", "DUFF_EAI")}

    assert check_rels(
        neo4j_session,
        "SnowflakeProcedure",
        "name",
        "SnowflakeSecret",
        "name",
        "USES_SECRET",
    ) == {("SCRAM_REACTOR", "DUFF_TOKEN")}
