from unittest.mock import patch

import cartography.intel.snowflake.catalog_integrations
from tests.data.snowflake.account import SNOWFLAKE_ACCOUNT_ID
from tests.data.snowflake.catalog_integrations import (
    SNOWFLAKE_CATALOG_INTEGRATION_ROLE_ARN,
)
from tests.data.snowflake.catalog_integrations import SNOWFLAKE_CATALOG_INTEGRATIONS
from tests.integration.cartography.intel.snowflake.test_account import (
    _ensure_local_neo4j_has_test_account,
)
from tests.integration.cartography.intel.snowflake.test_account import build_test_client
from tests.integration.cartography.intel.snowflake.test_account import TEST_UPDATE_TAG
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

GLUE_CATALOG_ID = "SPRINGFIELD.NUCLEAR/catalog_integration/SPRINGFIELD_GLUE_CATALOG"
REST_CATALOG_ID = "SPRINGFIELD.NUCLEAR/catalog_integration/DUFF_REST_CATALOG"


@patch.object(
    cartography.intel.snowflake.catalog_integrations,
    "get",
    return_value=SNOWFLAKE_CATALOG_INTEGRATIONS,
)
def test_sync_snowflake_catalog_integrations(mock_get, neo4j_session):
    # Arrange: the IAM role Snowflake assumes to read Glue belongs to the aws module.
    _ensure_local_neo4j_has_test_account(neo4j_session)
    neo4j_session.run(
        "MERGE (p:AWSPrincipal{arn: $arn}) SET p.lastupdated = $tag",
        arn=SNOWFLAKE_CATALOG_INTEGRATION_ROLE_ARN,
        tag=TEST_UPDATE_TAG,
    )

    # Act
    complete = cartography.intel.snowflake.catalog_integrations.sync(
        neo4j_session,
        build_test_client(),
        {"UPDATE_TAG": TEST_UPDATE_TAG, "ACCOUNT_ID": SNOWFLAKE_ACCOUNT_ID},
    )

    # Assert: the nested catalog, rest_config and rest_authentication objects are
    # flattened onto the node.
    assert complete is True
    assert check_nodes(
        neo4j_session,
        "SnowflakeCatalogIntegration",
        [
            "id",
            "name",
            "enabled",
            "catalog_source",
            "glue_catalog_id",
            "rest_catalog_uri",
            "oauth_client_id",
        ],
    ) == {
        (
            GLUE_CATALOG_ID,
            "SPRINGFIELD_GLUE_CATALOG",
            True,
            "GLUE",
            "000000000000",
            None,
            None,
        ),
        (
            REST_CATALOG_ID,
            "DUFF_REST_CATALOG",
            False,
            "POLARIS",
            None,
            "https://catalog.duff.example.com/v1",
            "duff-catalog-client",
        ),
    }
    # The OAuth client secret is never carried onto the node.
    assert not [
        key
        for record in neo4j_session.run(
            "MATCH (i:SnowflakeCatalogIntegration) RETURN properties(i) AS props",
        )
        for key in record["props"]
        if "secret" in key
    ]
    assert check_rels(
        neo4j_session,
        "SnowflakeCatalogIntegration",
        "id",
        "SnowflakeAccount",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        (GLUE_CATALOG_ID, SNOWFLAKE_ACCOUNT_ID),
        (REST_CATALOG_ID, SNOWFLAKE_ACCOUNT_ID),
    }
    # The cross-cloud payoff: the Glue-backed catalog is joined to the IAM role that
    # reads the customer's Data Catalog.
    assert check_rels(
        neo4j_session,
        "SnowflakeCatalogIntegration",
        "id",
        "AWSPrincipal",
        "arn",
        "ASSUMES_ROLE",
        rel_direction_right=True,
    ) == {(GLUE_CATALOG_ID, SNOWFLAKE_CATALOG_INTEGRATION_ROLE_ARN)}
