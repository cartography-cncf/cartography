"""Raw Snowflake view payloads.

Shaped as `GET /api/v2/databases/{db}/schemas/{schema}/views` returns them.
"""

from typing import Any

SNOWFLAKE_VIEWS: list[dict[str, Any]] = [
    # A secure view: its definition is hidden and the optimizer cannot leak the
    # rows it filters out.
    {
        "name": "SAFETY_INSPECTIONS",
        "database_name": "SPRINGFIELD",
        "schema_name": "NUCLEAR_PLANT",
        "kind": "VIEW",
        "secure": True,
        "query": (
            "SELECT reading_id, core_temp_c FROM reactor_readings "
            "WHERE core_temp_c < 500"
        ),
        "columns": [
            {"name": "READING_ID", "datatype": "NUMBER(38,0)", "nullable": False},
            {"name": "CORE_TEMP_C", "datatype": "FLOAT", "nullable": True},
        ],
        "owner": "SAFETY_INSPECTOR",
        "owner_role_type": "ROLE",
        "comment": "Only the readings cleared for publication",
        "created_on": "2026-08-03T15:55:00.000+00:00",
    },
    # A non-secure view over the same table, which is what makes it interesting.
    {
        "name": "DONUT_INVENTORY",
        "database_name": "SPRINGFIELD",
        "schema_name": "KWIK_E_MART",
        "kind": "VIEW",
        "secure": False,
        "query": "SELECT flavor, count(*) FROM squishee_sales GROUP BY flavor",
        "columns": [
            {"name": "FLAVOR", "datatype": "VARCHAR(64)", "nullable": True},
            {"name": "COUNT", "datatype": "NUMBER(38,0)", "nullable": False},
        ],
        "owner": "SHOPKEEPER",
        "owner_role_type": "ROLE",
        "comment": None,
        "created_on": "2026-08-03T15:56:00.000+00:00",
    },
]
