from unittest.mock import patch

import cartography.intel.snowflake.databases
from tests.data.snowflake.account import SNOWFLAKE_ACCOUNT_ID
from tests.data.snowflake.databases import SNOWFLAKE_DATABASES
from tests.integration.cartography.intel.snowflake.test_account import (
    _ensure_local_neo4j_has_test_account,
)
from tests.integration.cartography.intel.snowflake.test_account import build_test_client
from tests.integration.cartography.intel.snowflake.test_account import TEST_UPDATE_TAG
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

# The account's own databases: the subset whose schemas get walked.
LOCAL_DATABASES = [
    database
    for database in SNOWFLAKE_DATABASES
    if database["name"] in ("SPRINGFIELD", "MONORAIL")
]

SPRINGFIELD_DATABASE_ID = "SPRINGFIELD.NUCLEAR/database/SPRINGFIELD"
MONORAIL_DATABASE_ID = "SPRINGFIELD.NUCLEAR/database/MONORAIL"


def _ensure_local_neo4j_has_test_databases(neo4j_session) -> None:
    """Seed the Snowflake databases the schema-level syncs walk."""
    _ensure_local_neo4j_has_test_account(neo4j_session)
    with patch.object(
        cartography.intel.snowflake.databases,
        "get",
        return_value=LOCAL_DATABASES,
    ):
        cartography.intel.snowflake.databases.sync(
            neo4j_session,
            build_test_client(),
            None,
            {"UPDATE_TAG": TEST_UPDATE_TAG, "ACCOUNT_ID": SNOWFLAKE_ACCOUNT_ID},
        )


@patch.object(
    cartography.intel.snowflake.databases,
    "get",
    return_value=LOCAL_DATABASES,
)
def test_sync_snowflake_databases(mock_get, neo4j_session):
    # Arrange
    _ensure_local_neo4j_has_test_account(neo4j_session)
    client = build_test_client()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ACCOUNT_ID": SNOWFLAKE_ACCOUNT_ID,
    }

    # Act
    databases, complete = cartography.intel.snowflake.databases.sync(
        neo4j_session, client, None, common_job_parameters
    )

    # Assert: the listing is one account-level request, so it is always complete.
    assert complete is True
    assert [database["name"] for database in databases] == ["SPRINGFIELD", "MONORAIL"]

    assert check_nodes(
        neo4j_session,
        "SnowflakeDatabase",
        [
            "id",
            "name",
            "qualified_name",
            "is_from_share",
            "data_retention_time_in_days",
        ],
    ) == {
        (SPRINGFIELD_DATABASE_ID, "SPRINGFIELD", "SPRINGFIELD", False, 1),
        (MONORAIL_DATABASE_ID, "MONORAIL", "MONORAIL", False, 0),
    }

    # The ontology Database label makes the node reachable from cross-provider
    # data-store queries.
    assert check_nodes(neo4j_session, "Database", ["id"]) >= {
        (SPRINGFIELD_DATABASE_ID,),
        (MONORAIL_DATABASE_ID,),
    }

    # A database is grantable, so it carries the shared securable label.
    assert check_nodes(neo4j_session, "SnowflakeSecurable", ["id"]) >= {
        (SPRINGFIELD_DATABASE_ID,),
        (MONORAIL_DATABASE_ID,),
    }

    # Assert the sub-resource edge points at the account, not at anything else.
    assert check_rels(
        neo4j_session,
        "SnowflakeAccount",
        "id",
        "SnowflakeDatabase",
        "id",
        "RESOURCE",
    ) == {
        (SNOWFLAKE_ACCOUNT_ID, SPRINGFIELD_DATABASE_ID),
        (SNOWFLAKE_ACCOUNT_ID, MONORAIL_DATABASE_ID),
    }


@patch.object(
    cartography.intel.snowflake.databases,
    "get",
    return_value=[
        database
        for database in SNOWFLAKE_DATABASES
        if database["name"] == "SHELBYVILLE_FEED"
    ],
)
def test_sync_snowflake_shared_database_links_to_its_share(mock_get, neo4j_session):
    # Arrange: the share node is owned by the share sync, so seed it here.
    _ensure_local_neo4j_has_test_account(neo4j_session)
    share_id = "SPRINGFIELD.NUCLEAR/share/SHELBYVILLE_ACCT.MONORAIL_SHARE"
    neo4j_session.run("MERGE (share:SnowflakeShare {id: $share_id})", share_id=share_id)

    # Act
    cartography.intel.snowflake.databases.sync(
        neo4j_session,
        build_test_client(),
        {"SHELBYVILLE_FEED"},
        {"UPDATE_TAG": TEST_UPDATE_TAG, "ACCOUNT_ID": SNOWFLAKE_ACCOUNT_ID},
    )

    # Assert: the database is flagged as somebody else's data and linked to the
    # share it came in on.
    assert check_nodes(
        neo4j_session, "SnowflakeDatabase", ["name", "is_from_share", "origin"]
    ) >= {("SHELBYVILLE_FEED", True, "SHELBYVILLE_ACCT.MONORAIL_SHARE")}
    assert check_rels(
        neo4j_session,
        "SnowflakeDatabase",
        "name",
        "SnowflakeShare",
        "id",
        "CREATED_FROM_SHARE",
    ) == {("SHELBYVILLE_FEED", share_id)}


@patch.object(
    cartography.intel.snowflake.databases,
    "get",
    return_value=SNOWFLAKE_DATABASES,
)
def test_sync_inventories_every_database_but_walks_only_local_ones(
    mock_get, neo4j_session
):
    # Arrange
    _ensure_local_neo4j_has_test_account(neo4j_session)

    # Act
    walkable, _ = cartography.intel.snowflake.databases.sync(
        neo4j_session,
        build_test_client(),
        None,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "ACCOUNT_ID": SNOWFLAKE_ACCOUNT_ID},
    )

    # Assert: every database is inventoried, including Snowflake's own and the ones
    # mounted from an inbound share. A share arriving in the account is a
    # security-relevant fact, so dropping those nodes would hide it.
    assert {
        name for (name,) in check_nodes(neo4j_session, "SnowflakeDatabase", ["name"])
    } == {
        "SPRINGFIELD",
        "MONORAIL",
        "SNOWFLAKE",
        "SNOWFLAKE_SAMPLE_DATA",
        "SHELBYVILLE_FEED",
    }

    # Assert: only the account's own databases are walked, because descending into
    # a Snowflake-managed or shared database answers 403 for most roles.
    assert [database["name"] for database in walkable] == ["SPRINGFIELD", "MONORAIL"]


@patch.object(
    cartography.intel.snowflake.databases,
    "get",
    return_value=SNOWFLAKE_DATABASES,
)
def test_sync_honours_the_configured_allowlist_for_the_walk(mock_get, neo4j_session):
    # Arrange
    _ensure_local_neo4j_has_test_account(neo4j_session)

    # Act: an allowlist is exhaustive, so a shared database can be opted into.
    walkable, _ = cartography.intel.snowflake.databases.sync(
        neo4j_session,
        build_test_client(),
        {"MONORAIL", "SHELBYVILLE_FEED"},
        {"UPDATE_TAG": TEST_UPDATE_TAG, "ACCOUNT_ID": SNOWFLAKE_ACCOUNT_ID},
    )

    # Assert: the allowlist narrows the walk without narrowing the inventory.
    assert [database["name"] for database in walkable] == [
        "MONORAIL",
        "SHELBYVILLE_FEED",
    ]
    assert len(check_nodes(neo4j_session, "SnowflakeDatabase", ["name"])) == len(
        SNOWFLAKE_DATABASES
    )
