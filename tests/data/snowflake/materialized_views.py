"""Raw `SHOW MATERIALIZED VIEWS IN DATABASE` rows.

The SQL API returns every cell as a string keyed by the lowercased column name, which
is why the booleans and counts below are strings.
"""

from typing import Any

SNOWFLAKE_MATERIALIZED_VIEWS: list[dict[str, Any]] = [
    {
        "created_on": "1785000000.000000000 0",
        "name": "DAILY_MELTDOWN_RISK",
        "database_name": "SPRINGFIELD",
        "schema_name": "NUCLEAR_PLANT",
        "cluster_by": "LINEAR(DAY)",
        "rows": "365",
        "bytes": "24576",
        "source_database_name": "SPRINGFIELD",
        "source_schema_name": "NUCLEAR_PLANT",
        "source": "REACTOR_READINGS",
        "refreshed_on": "1785003600.000000000 0",
        "compacted_on": "1785003600.000000000 0",
        "owner": "PLANT_ENGINEER",
        "invalid": "false",
        "invalid_reason": None,
        "owner_role_type": "ROLE",
        "budget": None,
        "comment": "Risk score per day",
        "text": (
            "SELECT date_trunc('day', recorded_at) AS day, max(core_temp_c) "
            "FROM reactor_readings GROUP BY 1"
        ),
        "automatic_clustering": "true",
        "is_secure": "false",
    },
    # Invalidated, so queries silently fall back to the base table.
    {
        "created_on": "1785000060.000000000 0",
        "name": "SQUISHEE_TOTALS",
        "database_name": "SPRINGFIELD",
        "schema_name": "KWIK_E_MART",
        "cluster_by": "",
        "rows": "12",
        "bytes": "4096",
        "source_database_name": "SPRINGFIELD",
        "source_schema_name": "KWIK_E_MART",
        "source": "SQUISHEE_SALES",
        "refreshed_on": "1785000060.000000000 0",
        "compacted_on": None,
        "owner": "SHOPKEEPER",
        "invalid": "true",
        "invalid_reason": "Base table altered",
        "owner_role_type": "ROLE",
        "budget": None,
        "comment": None,
        "text": "SELECT flavor, sum(1) FROM squishee_sales GROUP BY flavor",
        "automatic_clustering": "false",
        "is_secure": "true",
    },
]
