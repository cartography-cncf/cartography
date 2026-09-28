"""Raw Snowflake resource monitor rows, as `SHOW RESOURCE MONITORS` returns them.

The SQL API renders every column as a string, thresholds as percentages, and
timestamps as epoch-seconds-with-offset, which is why the fixture is all strings.
"""

from typing import Any

SNOWFLAKE_RESOURCE_MONITORS: list[dict[str, Any]] = [
    {
        "name": "PLANT_BUDGET_MONITOR",
        "credit_quota": "5000",
        "used_credits": "1234.5",
        "remaining_credits": "3765.5",
        "level": "WAREHOUSE",
        "frequency": "MONTHLY",
        "start_time": "1785000000.000000000 0",
        "end_time": "",
        "notify_at": "75%,90%",
        "suspend_at": "100%",
        "suspend_immediate_at": "110%",
        "owner": "ACCOUNTADMIN",
        "comment": "Sector 7-G credit ceiling",
        "created_on": "1784000000.000000000 0",
    },
    # An account-level monitor that only notifies: it never suspends anything, so it
    # is a reporting control rather than a spending control.
    {
        "name": "DUFF_MONITOR",
        "credit_quota": "100",
        "used_credits": "99",
        "remaining_credits": "1",
        "level": "ACCOUNT",
        "frequency": "DAILY",
        "start_time": "1785000000.000000000 0",
        "end_time": "",
        "notify_at": "50%",
        "suspend_at": "",
        "suspend_immediate_at": "",
        "owner": "ACCOUNTADMIN",
        "comment": "",
        "created_on": "1784100000.000000000 0",
    },
]
