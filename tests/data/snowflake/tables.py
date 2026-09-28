"""Raw Snowflake table payloads.

Shaped as `GET /api/v2/databases/{db}/schemas/{schema}/tables` returns them, including
the `columns` list the transform collapses into a count.
"""

from typing import Any

SNOWFLAKE_TABLES: list[dict[str, Any]] = [
    {
        "name": "REACTOR_READINGS",
        "database_name": "SPRINGFIELD",
        "schema_name": "NUCLEAR_PLANT",
        "kind": "TABLE",
        "table_type": "NORMAL",
        "rows": 480000,
        "bytes": 12582912,
        "owner": "SYSADMIN",
        "owner_role_type": "ROLE",
        "comment": "Core temperature samples",
        "columns": [
            {"name": "READING_ID", "datatype": "NUMBER(38,0)", "nullable": False},
            {"name": "CORE_TEMP_C", "datatype": "FLOAT", "nullable": True},
            {"name": "RECORDED_AT", "datatype": "TIMESTAMP_LTZ(9)", "nullable": True},
        ],
        "constraints": [],
        "cluster_by": "LINEAR(RECORDED_AT)",
        "change_tracking": True,
        "enable_schema_evolution": False,
        "search_optimization": False,
        "data_retention_time_in_days": 1,
        "created_on": "2026-08-03T15:50:00.000+00:00",
        "dropped_on": None,
    },
    {
        "name": "SQUISHEE_SALES",
        "database_name": "SPRINGFIELD",
        "schema_name": "KWIK_E_MART",
        "kind": "TABLE",
        "table_type": "NORMAL",
        "rows": 1200,
        "bytes": 40960,
        "owner": "SHOPKEEPER",
        "owner_role_type": "ROLE",
        "comment": None,
        "columns": [
            {"name": "SALE_ID", "datatype": "NUMBER(38,0)", "nullable": False},
            {"name": "FLAVOR", "datatype": "VARCHAR(64)", "nullable": True},
        ],
        "constraints": [],
        "cluster_by": "",
        "change_tracking": False,
        # Schema evolution lets a loaded file widen the table without any DDL.
        "enable_schema_evolution": True,
        "search_optimization": False,
        "data_retention_time_in_days": 0,
        "created_on": "2026-08-03T15:51:00.000+00:00",
        "dropped_on": None,
    },
]
