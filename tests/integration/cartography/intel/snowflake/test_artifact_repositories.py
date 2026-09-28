from unittest.mock import patch

import cartography.intel.snowflake.artifact_repositories
from tests.data.snowflake.account import SNOWFLAKE_ACCOUNT_ID
from tests.data.snowflake.artifact_repositories import SNOWFLAKE_ARTIFACT_REPOSITORIES
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
    cartography.intel.snowflake.artifact_repositories,
    "get",
    return_value=SNOWFLAKE_ARTIFACT_REPOSITORIES,
)
def test_sync_snowflake_artifact_repositories(mock_get, neo4j_session):
    # Arrange
    client = build_test_client()
    _ensure_local_neo4j_has_test_account(neo4j_session)
    seed_schema_level_dependencies(neo4j_session)
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ACCOUNT_ID": SNOWFLAKE_ACCOUNT_ID,
    }

    # Act
    complete = cartography.intel.snowflake.artifact_repositories.sync(
        neo4j_session, client, TEST_SCHEMAS, common_job_parameters
    )

    # Assert
    assert complete is True
    assert check_nodes(
        neo4j_session, "SnowflakeArtifactRepository", ["name", "repository_type"]
    ) == {
        ("DUFF_PYPI", "PIP"),
        ("KWIK_E_PYPI", "PIP"),
    }

    assert check_rels(
        neo4j_session,
        "SnowflakeAccount",
        "id",
        "SnowflakeArtifactRepository",
        "name",
        "RESOURCE",
    ) == {
        (SNOWFLAKE_ACCOUNT_ID, "DUFF_PYPI"),
        (SNOWFLAKE_ACCOUNT_ID, "KWIK_E_PYPI"),
    }

    assert check_rels(
        neo4j_session,
        "SnowflakeSchema",
        "name",
        "SnowflakeArtifactRepository",
        "name",
        "CONTAINS",
    ) == {
        (TEST_SCHEMA_NAME, "DUFF_PYPI"),
        (TEST_SCHEMA_NAME, "KWIK_E_PYPI"),
    }

    # Only the repository that proxies an external index names an integration.
    assert check_rels(
        neo4j_session,
        "SnowflakeArtifactRepository",
        "name",
        "SnowflakeApiIntegration",
        "name",
        "USES_INTEGRATION",
    ) == {("DUFF_PYPI", "DUFF_API")}
