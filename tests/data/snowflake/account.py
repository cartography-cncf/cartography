"""Raw Snowflake account payloads, shaped as `GET /api/v2/accounts` returns them."""

from typing import Any

SNOWFLAKE_ACCOUNT_ID = "SPRINGFIELD.NUCLEAR"

# The account securable is named by its locator, not by the account identifier,
# which is why grants on the account cannot be resolved from the payload name.
SNOWFLAKE_ACCOUNT_LOCATOR = "AB12345"

SNOWFLAKE_ACCOUNTS: list[dict[str, Any]] = [
    {
        "organization_name": "SPRINGFIELD",
        "name": "NUCLEAR",
        "region_group": "PUBLIC",
        "region": "AWS_US_EAST_2",
        "edition": "ENTERPRISE",
        "created_on": "2026-08-03T15:28:07.370+00:00",
        "account_url": "https://springfield-nuclear.snowflakecomputing.com",
        "account_locator": SNOWFLAKE_ACCOUNT_LOCATOR,
        "account_locator_url": "https://ab12345.us-east-2.aws.snowflakecomputing.com",
        "managed_accounts": 1,
        "comment": "Sector 7-G",
        "is_org_admin": True,
        "retention_time": 1,
        "dropped_on": None,
        "scheduled_deletion_time": None,
    },
    # A sibling account in the same organization. It is recorded as a node so that
    # share and replication targets resolve, but its objects are never synced.
    {
        "organization_name": "SPRINGFIELD",
        "name": "KWIKEMART",
        "region_group": "PUBLIC",
        "region": "AWS_US_WEST_2",
        "edition": "STANDARD",
        "created_on": "2026-08-03T15:30:00.000+00:00",
        "account_url": "https://springfield-kwikemart.snowflakecomputing.com",
        "account_locator": "CD67890",
        "is_org_admin": False,
        "retention_time": 1,
        "dropped_on": None,
        "scheduled_deletion_time": None,
    },
]

SNOWFLAKE_MANAGED_ACCOUNTS: list[dict[str, Any]] = [
    {
        "name": "SHELBYVILLE_READER",
        "cloud": "AWS",
        "region": "us-east-2",
        "account_locator": "EF13579",
        "account_locator_url": "https://ef13579.us-east-2.aws.snowflakecomputing.com",
        "account_type": "READER",
        "created_on": "2026-08-03T15:35:00.000+00:00",
        "comment": "Reader account for the Shelbyville data share",
    },
]
