"""Raw Snowflake stored procedure payloads.

Shaped as `GET /api/v2/databases/{db}/schemas/{schema}/procedures` returns them:
one owner-rights procedure, which lends its owner's privileges to every caller,
and one caller-rights procedure, which does not.
"""

from typing import Any

SNOWFLAKE_PROCEDURES: list[dict[str, Any]] = [
    {
        "name": "SCRAM_REACTOR",
        "signature": [{"name": "REASON", "datatype": "VARCHAR"}],
        "returns": "VARCHAR",
        "language": "PYTHON",
        "execute_as": "OWNER",
        "is_secure": False,
        "is_external_function": False,
        "is_memoizable": False,
        "is_builtin": False,
        "api_integration": None,
        "handler": "scram.run",
        "runtime_version": "3.11",
        "packages": ["snowflake-snowpark-python"],
        "imports": ["@PLANT_STAGE/scram.py"],
        "external_access_integrations": ["DUFF_EAI"],
        "secrets": {"cred": "SPRINGFIELD.NUCLEAR_PLANT.DUFF_TOKEN"},
        "owner": "PLANT_ENGINEER",
        "comment": "Shut the reactor down",
        "created_on": "2026-08-03T16:30:00.000+00:00",
    },
    {
        "name": "STIR_THE_POT",
        "signature": [],
        "returns": "VARCHAR",
        "language": "SQL",
        "execute_as": "CALLER",
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
        "comment": None,
        "created_on": "2026-08-03T16:31:00.000+00:00",
    },
]
