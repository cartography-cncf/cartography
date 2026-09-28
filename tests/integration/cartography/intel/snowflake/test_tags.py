from unittest.mock import patch

import cartography.intel.snowflake.tags
from tests.data.snowflake.account import SNOWFLAKE_ACCOUNT_ID
from tests.data.snowflake.tags import SNOWFLAKE_TAGS
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


@patch.object(cartography.intel.snowflake.tags, "get", return_value=SNOWFLAKE_TAGS)
def test_sync_snowflake_tags(mock_get, neo4j_session):
    # Arrange
    client = build_test_client()
    _ensure_local_neo4j_has_test_account(neo4j_session)
    seed_schema_level_dependencies(neo4j_session)
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ACCOUNT_ID": SNOWFLAKE_ACCOUNT_ID,
    }

    # Act
    complete = cartography.intel.snowflake.tags.sync(
        neo4j_session, client, TEST_SCHEMAS, common_job_parameters
    )

    # Assert
    assert complete is True
    assert check_nodes(neo4j_session, "SnowflakeTag", ["name", "owner"]) == {
        ("SAFETY_CLASSIFICATION", "PLANT_ENGINEER"),
        ("COST_CENTER", "SHOPKEEPER"),
    }

    # A tag with no allowed values accepts any string, so the empty list has to
    # survive the load rather than being dropped.
    allowed_values = {
        row["name"]: row["allowed_values"]
        for row in neo4j_session.run(
            "MATCH (t:SnowflakeTag) RETURN t.name AS name, "
            "t.allowed_values AS allowed_values",
        )
    }
    assert allowed_values == {
        "SAFETY_CLASSIFICATION": ["PUBLIC", "RESTRICTED", "SECRET"],
        "COST_CENTER": [],
    }

    # A tag definition carries no value, so it must not be labelled as an ontology
    # Tag, whose contract is a key/value pair.
    assert check_nodes(neo4j_session, "Tag", ["name"]) == set()

    assert check_rels(
        neo4j_session,
        "SnowflakeAccount",
        "id",
        "SnowflakeTag",
        "name",
        "RESOURCE",
    ) == {
        (SNOWFLAKE_ACCOUNT_ID, "SAFETY_CLASSIFICATION"),
        (SNOWFLAKE_ACCOUNT_ID, "COST_CENTER"),
    }

    assert check_rels(
        neo4j_session,
        "SnowflakeSchema",
        "name",
        "SnowflakeTag",
        "name",
        "CONTAINS",
    ) == {
        (TEST_SCHEMA_NAME, "SAFETY_CLASSIFICATION"),
        (TEST_SCHEMA_NAME, "COST_CENTER"),
    }
