"""Snowflake resource monitors.

There is no object endpoint for resource monitors, so they come from
``SHOW RESOURCE MONITORS`` through the SQL API. Every value arrives as a string,
and the quota-threshold columns arrive as percentages (``"75%"``), so they are
coerced here rather than stored as text.
"""

import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.snowflake.sql_values import to_text
from cartography.intel.snowflake.util import is_sql_unavailable
from cartography.intel.snowflake.util import iso_to_datetime
from cartography.intel.snowflake.util import sf_fqn
from cartography.intel.snowflake.util import sf_id
from cartography.intel.snowflake.util import SnowflakeClient
from cartography.intel.snowflake.util import SnowflakeSqlError
from cartography.intel.snowflake.util import warn_unavailable
from cartography.models.snowflake.resource_monitor import SnowflakeResourceMonitorSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


def _to_float(value: Any) -> float | None:
    """Parse a numeric SQL API column, which always arrives as a string."""
    if value in (None, ""):
        return None
    return float(value)


def _to_percent(value: Any) -> int | None:
    """Parse a single ``"NN%"`` threshold into an integer percentage."""
    if value in (None, ""):
        return None
    return int(str(value).strip().rstrip("%"))


def _to_percent_list(value: Any) -> list[int]:
    """Parse a comma-separated ``"75%,90%"`` threshold list."""
    if value in (None, ""):
        return []
    thresholds = (_to_percent(part) for part in str(value).split(","))
    return [threshold for threshold in thresholds if threshold is not None]


@timeit
def get(client: SnowflakeClient) -> list[dict[str, Any]] | None:
    """Return every resource monitor, or None when the SQL surface is unavailable."""
    try:
        return client.run_sql("SHOW RESOURCE MONITORS")
    except SnowflakeSqlError as error:
        if not is_sql_unavailable(error):
            raise
        warn_unavailable("resource monitors", "SHOW RESOURCE MONITORS is not permitted")
        return None


def transform(
    monitors: list[dict[str, Any]],
    account_id: str,
) -> list[dict[str, Any]]:
    transformed: list[dict[str, Any]] = []
    for monitor in monitors:
        name = monitor["name"]
        transformed.append(
            {
                "id": sf_id(account_id, "resource_monitor", sf_fqn(name)),
                "name": name,
                "credit_quota": _to_float(monitor.get("credit_quota")),
                "used_credits": _to_float(monitor.get("used_credits")),
                "remaining_credits": _to_float(monitor.get("remaining_credits")),
                "level": to_text(monitor.get("level")),
                "frequency": to_text(monitor.get("frequency")),
                "notify_at": _to_percent_list(monitor.get("notify_at")),
                "suspend_at": _to_percent(monitor.get("suspend_at")),
                "suspend_immediate_at": _to_percent(
                    monitor.get("suspend_immediate_at")
                ),
                "owner": to_text(monitor.get("owner")),
                "comment": to_text(monitor.get("comment")),
                "created_on": iso_to_datetime(monitor.get("created_on")),
                "start_time": iso_to_datetime(monitor.get("start_time")),
                "end_time": iso_to_datetime(monitor.get("end_time")),
            },
        )
    return transformed


def load_resource_monitors(
    neo4j_session: neo4j.Session,
    monitors: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SnowflakeResourceMonitorSchema(),
        monitors,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: dict) -> None:
    GraphJob.from_node_schema(
        SnowflakeResourceMonitorSchema(), common_job_parameters
    ).run(neo4j_session)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: SnowflakeClient,
    common_job_parameters: dict,
) -> bool:
    """Sync Snowflake resource monitors.

    Runs before warehouses so a warehouse's MONITORED_BY edge resolves against a
    monitor node already in the graph.

    Returns whether the listing was readable. When it was not, the caller skips
    cleanup rather than deleting monitors it merely failed to re-read.
    """
    monitors = get(client)
    if monitors is None:
        return False

    transformed = transform(monitors, client.account_id)
    logger.info(
        "Loading %d Snowflake resource monitors for account %s.",
        len(transformed),
        client.account_id,
    )
    load_resource_monitors(
        neo4j_session,
        transformed,
        client.account_id,
        common_job_parameters["UPDATE_TAG"],
    )
    return True
