"""Raw Snowflake function payloads.

Shaped as `GET /api/v2/databases/{db}/schemas/{schema}/functions` and
`.../user-defined-functions` return them. `COOLANT_TEMP` appears twice with
different argument types, which is what forces the argument list into the node id.
"""

from typing import Any

SNOWFLAKE_FUNCTIONS: list[dict[str, Any]] = [
    {
        "name": "COOLANT_TEMP",
        "signature": [{"name": "ROD_ID", "datatype": "NUMBER(38,0)"}],
        "returns": "FLOAT",
        "language": "SQL",
        "is_secure": False,
        "is_external_function": False,
        "is_memoizable": False,
        "is_builtin": False,
        "api_integration": None,
        "handler": None,
        "runtime_version": None,
        "packages": [],
        "imports": [],
        "external_access_integrations": [],
        "secrets": {},
        "owner": "PLANT_ENGINEER",
        "comment": "Temperature of one control rod",
        "created_on": "2026-08-03T16:20:00.000+00:00",
    },
    {
        "name": "COOLANT_TEMP",
        "signature": [
            {"name": "ROD_ID", "datatype": "NUMBER(38,0)"},
            {"name": "SCALE", "datatype": "VARCHAR"},
        ],
        "returns": "FLOAT",
        "language": "SQL",
        "is_secure": True,
        "is_external_function": False,
        "is_memoizable": True,
        "is_builtin": False,
        "api_integration": None,
        "handler": None,
        "runtime_version": None,
        "packages": [],
        "imports": [],
        "external_access_integrations": [],
        "secrets": {},
        "owner": "PLANT_ENGINEER",
        "comment": "Temperature of one control rod, in the requested scale",
        "created_on": "2026-08-03T16:21:00.000+00:00",
    },
    {
        "name": "DUFF_LOOKUP",
        "signature": [{"name": "BREW", "datatype": "VARCHAR"}],
        "returns": "VARIANT",
        "language": "PYTHON",
        "is_secure": False,
        "is_external_function": True,
        "is_memoizable": False,
        "is_builtin": False,
        "api_integration": "DUFF_API",
        "handler": "duff.lookup",
        "runtime_version": "3.11",
        "packages": ["requests"],
        "imports": ["@DUFF_STAGE/duff.py"],
        "external_access_integrations": ["DUFF_EAI"],
        "secrets": {"cred": "SPRINGFIELD.NUCLEAR_PLANT.DUFF_TOKEN"},
        "owner": "PLANT_ENGINEER",
        "comment": "Ask the brewery what is on tap",
        "created_on": "2026-08-03T16:22:00.000+00:00",
    },
]
