"""Snowflake alerts: scheduled condition queries and the SQL they trigger."""

import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.snowflake.util import iso_to_datetime
from cartography.intel.snowflake.util import schedule_to_text
from cartography.intel.snowflake.util import sf_fqn
from cartography.intel.snowflake.util import sf_id
from cartography.intel.snowflake.util import sf_path_segment
from cartography.intel.snowflake.util import skip_or_raise_http
from cartography.intel.snowflake.util import SnowflakeClient
from cartography.models.snowflake.alert import SnowflakeAlertSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get(
    client: SnowflakeClient,
    database_name: str,
    schema_name: str,
) -> list[dict[str, Any]] | None:
    """Alerts in one schema, or None when the schema is not readable."""
    try:
        return client.list_all(
            f"/api/v2/databases/{sf_path_segment(database_name)}/schemas/{sf_path_segment(schema_name)}/alerts",
        )
    except requests.HTTPError as error:
        skip_or_raise_http(error, 403, 404)
        return None


def transform(
    alerts: list[dict[str, Any]],
    schema: dict[str, Any],
    account_id: str,
) -> list[dict[str, Any]]:
    database_name = schema["database_name"]
    schema_name = schema["name"]
    transformed: list[dict[str, Any]] = []

    for alert in alerts:
        name = alert["name"]
        qualified_name = sf_fqn(database_name, schema_name, name)
        warehouse = alert.get("warehouse")
        transformed.append(
            {
                "id": sf_id(account_id, "alert", qualified_name),
                "name": name,
                "qualified_name": qualified_name,
                "database_name": database_name,
                "schema_name": schema_name,
                "parent_schema_id": schema["id"],
                "warehouse": warehouse,
                "warehouse_id": (
                    sf_id(account_id, "warehouse", sf_fqn(warehouse))
                    if warehouse
                    else None
                ),
                "schedule": schedule_to_text(alert.get("schedule")),
                "state": alert.get("state"),
                "condition": alert.get("condition"),
                "action": alert.get("action"),
                "owner": alert.get("owner"),
                "comment": alert.get("comment"),
                "created_on": iso_to_datetime(alert.get("created_on")),
            },
        )
    return transformed


def load_alerts(
    neo4j_session: neo4j.Session,
    alerts: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SnowflakeAlertSchema(),
        alerts,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: dict) -> None:
    GraphJob.from_node_schema(SnowflakeAlertSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: SnowflakeClient,
    schemas: list[dict[str, Any]],
    common_job_parameters: dict,
) -> bool:
    """Sync every alert in every readable schema.

    Returns whether the walk was complete, so the caller can skip alert cleanup
    rather than deleting nodes it merely failed to re-read this run.
    """
    account_id = client.account_id
    alerts: list[dict[str, Any]] = []
    complete = True

    for schema in schemas:
        listing = get(client, schema["database_name"], schema["name"])
        if listing is None:
            complete = False
            continue
        alerts.extend(transform(listing, schema, account_id))

    logger.info(
        "Loading %d Snowflake alerts for account %s.",
        len(alerts),
        account_id,
    )
    load_alerts(neo4j_session, alerts, account_id, common_job_parameters["UPDATE_TAG"])

    if not complete:
        logger.warning(
            "Some Snowflake schemas could not be read for alerts; skipping alert "
            "cleanup so still-valid nodes are not deleted.",
        )
    return complete
