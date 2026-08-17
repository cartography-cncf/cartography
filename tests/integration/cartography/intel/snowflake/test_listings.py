from unittest.mock import patch

import cartography.intel.snowflake.listings
import cartography.intel.snowflake.shares
from tests.data.snowflake.account import SNOWFLAKE_ACCOUNT_ID
from tests.data.snowflake.listings import SNOWFLAKE_LISTINGS
from tests.data.snowflake.shares import SNOWFLAKE_SHARES
from tests.integration.cartography.intel.snowflake.test_account import (
    _ensure_local_neo4j_has_test_account,
)
from tests.integration.cartography.intel.snowflake.test_account import build_test_client
from tests.integration.cartography.intel.snowflake.test_account import TEST_UPDATE_TAG
from tests.integration.util import check_nodes
from tests.integration.util import check_rels


def _ensure_local_neo4j_has_test_shares(neo4j_session) -> None:
    shares, _ = cartography.intel.snowflake.shares.transform(
        SNOWFLAKE_SHARES, {}, {}, SNOWFLAKE_ACCOUNT_ID
    )
    cartography.intel.snowflake.shares.load_shares(
        neo4j_session, shares, SNOWFLAKE_ACCOUNT_ID, TEST_UPDATE_TAG
    )


@patch.object(
    cartography.intel.snowflake.listings, "get", return_value=SNOWFLAKE_LISTINGS
)
def test_sync_snowflake_listings(mock_get, neo4j_session):
    # Arrange
    client = build_test_client()
    _ensure_local_neo4j_has_test_account(neo4j_session)
    _ensure_local_neo4j_has_test_shares(neo4j_session)
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ACCOUNT_ID": SNOWFLAKE_ACCOUNT_ID,
    }

    # Act
    complete = cartography.intel.snowflake.listings.sync(
        neo4j_session, client, common_job_parameters
    )

    # Assert
    assert complete is True
    # A published EXTERNAL listing is public data exposure, which is only readable
    # from the state and distribution pair.
    assert check_nodes(
        neo4j_session,
        "SnowflakeListing",
        ["global_name", "state", "distribution", "is_monetized"],
    ) == {
        ("GZTDUFF0001", "PUBLISHED", "EXTERNAL", True),
        ("GZTDUFF0002", "DRAFT", "INTERNAL", False),
    }

    # An unset boolean column stays null rather than becoming false.
    assert check_nodes(
        neo4j_session,
        "SnowflakeListing",
        ["global_name", "is_limited_trial", "review_state"],
    ) == {
        ("GZTDUFF0001", False, "APPROVED"),
        ("GZTDUFF0002", None, None),
    }

    assert check_rels(
        neo4j_session,
        "SnowflakeListing",
        "global_name",
        "SnowflakeAccount",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        ("GZTDUFF0001", SNOWFLAKE_ACCOUNT_ID),
        ("GZTDUFF0002", SNOWFLAKE_ACCOUNT_ID),
    }

    # The draft listing publishes no share, so it gets no edge instead of one
    # pointing at nothing.
    assert check_rels(
        neo4j_session,
        "SnowflakeListing",
        "global_name",
        "SnowflakeShare",
        "name",
        "PUBLISHES",
        rel_direction_right=True,
    ) == {("GZTDUFF0001", "REACTOR_FEED")}
