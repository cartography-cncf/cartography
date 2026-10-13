import cartography.intel.snowflake.account
from tests.data.snowflake.account import SNOWFLAKE_ACCOUNT_ID


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
