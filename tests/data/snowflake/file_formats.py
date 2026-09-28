"""Raw `SHOW FILE FORMATS IN DATABASE` rows.

The SQL API returns every cell as a string keyed by the lowercased column name.
"""

from typing import Any

SNOWFLAKE_FILE_FORMATS: list[dict[str, Any]] = [
    {
        "created_on": "1785020000.000000000 0",
        "name": "LOG_CSV",
        "database_name": "SPRINGFIELD",
        "schema_name": "NUCLEAR_PLANT",
        "type": "CSV",
        "owner": "PLANT_ENGINEER",
        "comment": "Control-room log layout",
        "format_options": (
            '{"TYPE":"CSV","FIELD_DELIMITER":"|","SKIP_HEADER":1,'
            '"NULL_IF":["\\\\N"]}'
        ),
        "owner_role_type": "ROLE",
    },
    {
        "created_on": "1785020060.000000000 0",
        "name": "SHIPMENT_JSON",
        "database_name": "SPRINGFIELD",
        "schema_name": "KWIK_E_MART",
        "type": "JSON",
        "owner": "SHOPKEEPER",
        "comment": None,
        "format_options": '{"TYPE":"JSON","STRIP_OUTER_ARRAY":true}',
        "owner_role_type": "ROLE",
    },
]
