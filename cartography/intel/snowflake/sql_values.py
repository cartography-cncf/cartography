"""Coercion helpers for Snowflake SQL API result rows.

The SQL API returns every column as a string (or ``None``), keyed by the lowercased
column name, so a boolean arrives as ``'true'``, a number as ``'477'``, a list as a
comma-separated string, and an unset value as ``''``. Every governance surface in
this module reads from that same shape, so the coercions live here once rather than
being re-derived per module.
"""

import logging
from typing import Any

from cartography.intel.snowflake.util import is_sql_unavailable
from cartography.intel.snowflake.util import SnowflakeClient
from cartography.intel.snowflake.util import SnowflakeSqlError
from cartography.intel.snowflake.util import warn_unavailable

logger = logging.getLogger(__name__)


def to_text(value: Any) -> str | None:
    """Return a string column, mapping Snowflake's empty string to null.

    Snowflake writes "not set" as an empty string in ``SHOW`` output, and an empty
    string in the graph is indistinguishable from a deliberately blank value.
    """
    if value in (None, ""):
        return None
    return str(value)


def to_bool(value: Any) -> bool | None:
    """Return a boolean column, or null when the column is absent or unset."""
    if value in (None, ""):
        return None
    return str(value).lower() == "true"


def to_int(value: Any) -> int | None:
    """Return a numeric column, or null when the column is absent or unset."""
    if value in (None, ""):
        return None
    return int(float(value))


def describe_policy(
    client: SnowflakeClient,
    statement: str,
    resource: str,
) -> dict[str, Any] | None:
    """Run a ``DESCRIBE`` on a policy object and return its settings as one dict.

    Snowflake is not consistent about the shape of ``DESCRIBE`` output across policy
    kinds: some return a single wide row whose columns are the settings, and others
    return one row per setting with a name column and a value column. Both shapes
    are folded into a single mapping here so callers can read settings by name and
    treat a missing setting as null instead of crashing when Snowflake changes or
    extends the output.

    Returns ``None`` when the statement is not permitted, so the caller can skip the
    object rather than load it with every setting nulled out.
    """
    try:
        rows = client.run_sql(statement)
    except SnowflakeSqlError as error:
        if not is_sql_unavailable(error):
            raise
        warn_unavailable(resource, "DESCRIBE is not permitted")
        return None

    if not rows:
        return {}

    first_row = rows[0]
    key_column = next(
        (column for column in ("property", "name") if column in first_row), None
    )
    value_column = next(
        (column for column in ("property_value", "value") if column in first_row), None
    )
    if key_column and value_column:
        return {
            str(row[key_column]).lower(): row.get(value_column)
            for row in rows
            if row.get(key_column)
        }

    if len(rows) > 1:
        logger.debug(
            "DESCRIBE for %s returned %d rows in wide form; using the first.",
            resource,
            len(rows),
        )
    return dict(first_row)
