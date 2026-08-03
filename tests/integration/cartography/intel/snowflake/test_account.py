from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.snowflake.account
from tests.data.snowflake.account import SNOWFLAKE_ACCOUNT_ID
from tests.data.snowflake.account import SNOWFLAKE_ACCOUNTS
from tests.data.snowflake.account import SNOWFLAKE_MANAGED_ACCOUNTS
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


def build_test_client() -> MagicMock:
    """A stand-in Snowflake client carrying only what the syncs read off it."""
    client = MagicMock()
    client.account_id = SNOWFLAKE_ACCOUNT_ID
    return client


def _ensure_local_neo4j_has_test_account(neo4j_session) -> None:
    """Seed the SnowflakeAccount tenant node every other sync hangs off.

    Shared by the other Snowflake integration test modules, so that each one can
    exercise its own sync against a real tenant node instead of duplicating this.
    """
    accounts = cartography.intel.snowflake.account.transform_accounts(
        SNOWFLAKE_ACCOUNTS, SNOWFLAKE_ACCOUNT_ID
    )
    cartography.intel.snowflake.account.load_accounts(
        neo4j_session, accounts, TEST_UPDATE_TAG
    )


@patch.object(
    cartography.intel.snowflake.account,
    "get_managed_accounts",
    return_value=SNOWFLAKE_MANAGED_ACCOUNTS,
)
@patch.object(
    cartography.intel.snowflake.account,
    "get_organization_accounts",
    return_value=SNOWFLAKE_ACCOUNTS,
)
def test_sync_snowflake_accounts(mock_accounts, mock_managed, neo4j_session):
    # Arrange
    client = build_test_client()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "ACCOUNT_ID": SNOWFLAKE_ACCOUNT_ID,
    }

    # Act
    cartography.intel.snowflake.account.sync(
        neo4j_session, client, common_job_parameters
    )

    # Assert: both accounts in the organization are recorded, and only the
    # connected one is marked current.
    assert check_nodes(
        neo4j_session, "SnowflakeAccount", ["id", "name", "edition", "is_current"]
    ) == {
        ("SPRINGFIELD.NUCLEAR", "NUCLEAR", "ENTERPRISE", True),
        ("SPRINGFIELD.KWIKEMART", "KWIKEMART", "STANDARD", False),
    }

    # The account is a Tenant, so cross-provider tenant queries can reach it.
    assert ("SPRINGFIELD.NUCLEAR",) in check_nodes(neo4j_session, "Tenant", ["id"])

    # Account-level grants target the account, so it must be a grantable object.
    assert ("SPRINGFIELD.NUCLEAR",) in check_nodes(
        neo4j_session, "SnowflakeSecurable", ["id"]
    )

    # Assert the organization node and its edge to both accounts.
    assert check_nodes(neo4j_session, "SnowflakeOrganization", ["id"]) == {
        ("SPRINGFIELD",),
    }
    assert check_rels(
        neo4j_session,
        "SnowflakeOrganization",
        "id",
        "SnowflakeAccount",
        "id",
        "RESOURCE",
    ) == {
        ("SPRINGFIELD", "SPRINGFIELD.NUCLEAR"),
        ("SPRINGFIELD", "SPRINGFIELD.KWIKEMART"),
    }

    # Assert the reader account hangs off the account that created it.
    assert check_nodes(
        neo4j_session, "SnowflakeManagedAccount", ["name", "is_reader"]
    ) == {("SHELBYVILLE_READER", True)}
    assert check_rels(
        neo4j_session,
        "SnowflakeAccount",
        "id",
        "SnowflakeManagedAccount",
        "name",
        "RESOURCE",
    ) == {("SPRINGFIELD.NUCLEAR", "SHELBYVILLE_READER")}


def test_transform_accounts_emits_the_connected_account_without_orgadmin():
    # Arrange: ORGADMIN is not held, so the listing is unavailable.
    # Act
    accounts = cartography.intel.snowflake.account.transform_accounts(
        None, SNOWFLAKE_ACCOUNT_ID
    )

    # Assert: the tenant node still exists, built from the identifier alone, so
    # every other sync has something to attach to.
    assert accounts == [
        {
            "id": "SPRINGFIELD.NUCLEAR",
            "name": "NUCLEAR",
            "organization_name": "SPRINGFIELD",
            "edition": None,
            "region": None,
            "region_group": None,
            "account_url": None,
            "account_locator": None,
            "is_org_admin": None,
            "retention_time": None,
            "comment": None,
            "created_on": None,
            "dropped_on": None,
            "scheduled_deletion_time": None,
            "is_current": True,
        },
    ]
