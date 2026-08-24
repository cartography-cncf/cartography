"""Raw Snowflake Cortex Search service payloads.

Shaped as `GET /api/v2/databases/{db}/schemas/{schema}/cortex-search-services`
returns them: one service indexing a single table, and one built over a query,
which has no table to point at.
"""

from typing import Any

SNOWFLAKE_CORTEX_SEARCH_SERVICES: list[dict[str, Any]] = [
    {
        "name": "REACTOR_LOG_SEARCH",
        "target_lag": "1 hour",
        "warehouse": "SECTOR_7G_WH",
        "source": "SPRINGFIELD.NUCLEAR_PLANT.REACTOR_READINGS",
        "embedding_model": "snowflake-arctic-embed-m-v1.5",
        "attribute_columns": ["READING_ID"],
        "search_column": "OPERATOR_NOTES",
        "service_query_url": (
            "https://springfield-nuclear.snowflakecomputing.com/api/v2/databases/"
            "SPRINGFIELD/schemas/NUCLEAR_PLANT/cortex-search-services/"
            "REACTOR_LOG_SEARCH:query"
        ),
        "comment": "Search what the operators wrote down",
        "created_on": "2026-08-03T17:20:00.000+00:00",
    },
    {
        "name": "SAFETY_MEMO_SEARCH",
        "target_lag": "1 day",
        "warehouse": None,
        "source": "SELECT MEMO_TEXT FROM SAFETY_MEMOS WHERE ARCHIVED = FALSE",
        "embedding_model": "snowflake-arctic-embed-m-v1.5",
        "attribute_columns": [],
        "search_column": "MEMO_TEXT",
        "service_query_url": None,
        "comment": None,
        "created_on": "2026-08-03T17:21:00.000+00:00",
    },
]
