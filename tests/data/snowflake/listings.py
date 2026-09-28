"""SHOW LISTINGS rows, as the SQL API returns them."""

from typing import Any

SNOWFLAKE_LISTINGS: list[dict[str, Any]] = [
    {
        # Published on the public Marketplace, which makes the share behind it a
        # public data exposure.
        "global_name": "GZTDUFF0001",
        "name": "REACTOR_FEED_LISTING",
        "title": "Reactor telemetry",
        "state": "PUBLISHED",
        "review_state": "APPROVED",
        "distribution": "EXTERNAL",
        "is_monetized": "true",
        "is_application": "false",
        "is_targeted": "false",
        "is_limited_trial": "false",
        "share_name": "REACTOR_FEED",
        "published_on": "1783000000.000",
        "owner": "ACCOUNTADMIN",
        "comment": None,
        "created_on": "1782900000.000",
    },
    {
        "global_name": "GZTDUFF0002",
        "name": "DONUT_APP_DRAFT",
        "title": "Donut inventory app",
        "state": "DRAFT",
        "review_state": "",
        "distribution": "INTERNAL",
        "is_monetized": "false",
        "is_application": "true",
        "is_targeted": "true",
        "is_limited_trial": "",
        "share_name": "",
        "published_on": None,
        "owner": "ACCOUNTADMIN",
        "comment": "not published yet",
        "created_on": "1783100000.000",
    },
]
