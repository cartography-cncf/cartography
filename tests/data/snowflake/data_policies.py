"""Data governance policy listing rows, SQL-API shaped.

This is the shape ``data_policies.get()`` returns: each ``SHOW`` row with the
``policy_kind`` it was collected from attached.
"""

from typing import Any

SNOWFLAKE_DATA_POLICIES: list[dict[str, Any]] = [
    {
        "created_on": "1780900000.000",
        "name": "MASK_EMPLOYEE_ID",
        "database_name": "SPRINGFIELD",
        "schema_name": "NUCLEAR_PLANT",
        "kind": "MASKING_POLICY",
        "signature": "(VAL VARCHAR)",
        "return_type": "VARCHAR(16777216)",
        "body": "CASE WHEN CURRENT_ROLE() = 'SAFETY_INSPECTOR' THEN '***' ELSE VAL END",
        "owner": "SAFETY_INSPECTOR",
        "owner_role_type": "ROLE",
        "comment": "mask the operator employee id",
        "policy_kind": "MASKING_POLICY",
    },
    {
        "created_on": "1781000000.000",
        "name": "SECTOR_ROWS",
        "database_name": "SPRINGFIELD",
        "schema_name": "NUCLEAR_PLANT",
        "kind": "ROW_ACCESS_POLICY",
        "signature": "(SECTOR VARCHAR)",
        "return_type": "BOOLEAN",
        "body": "SECTOR = '7G'",
        "owner": "SAFETY_INSPECTOR",
        "owner_role_type": "ROLE",
        "comment": None,
        "policy_kind": "ROW_ACCESS_POLICY",
    },
    {
        "created_on": "1781100000.000",
        "name": "NO_PROJECT_BADGE",
        "database_name": "SPRINGFIELD",
        "schema_name": "NUCLEAR_PLANT",
        "kind": "PROJECTION_POLICY",
        "owner": "SAFETY_INSPECTOR",
        "owner_role_type": "ROLE",
        "comment": "",
        "policy_kind": "PROJECTION_POLICY",
    },
]
