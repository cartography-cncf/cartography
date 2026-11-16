import logging
import re
from collections.abc import Iterable
from collections.abc import Iterator
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.sentra import api
from cartography.models.sentra.alert import SentraAlertSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

# Cleanup removes alerts that Sentra resolved or ignored, so a sync fetches only the
# statuses that still need attention.
ACTIVE_ALERT_STATUSES = ["pending", "opened", "in_progress"]

_AWS_ROLE_ARN_RE = re.compile(r"^arn:aws(?:-[a-z]+)*:iam::\d{12}:role/.+$")


@timeit
def get(session: requests.Session, api_url: str) -> Iterator[list[dict[str, Any]]]:
    yield from api.iter_search_pages(
        session,
        api_url,
        api.ALERTS_SEARCH_PATH,
        filters={"status": {"op": "EQ", "values": ACTIVE_ALERT_STATUSES}},
    )


def transform(raw_alerts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for alert in raw_alerts:
        entity_type = alert["entity_type"]
        entity = alert.get("entity") or {}
        cloud_unique_id = entity.get("cloud_unique_id")
        result.append(
            {
                "id": alert["id"],
                "name": alert["name"],
                "description": alert.get("description"),
                "recommendation": alert.get("recommendation"),
                "severity": alert["severity"],
                "status": alert["status"],
                "status_reason": alert.get("status_reason"),
                "alert_type": alert["type"],
                "risk_type": alert.get("risk_type"),
                "policy_id": alert["policy_id"],
                "policy_type": alert.get("Policy__type"),
                "frameworks": alert.get("frameworks") or [],
                "tags": alert.get("tags") or [],
                "entity_type": entity_type,
                "entity_id": alert["entity_id"],
                "entity_name": entity.get("name"),
                "entity_cloud_unique_id": cloud_unique_id,
                "connector_id": alert["connector_id"],
                "connector_account_id": alert.get("Connector__account_id"),
                "connector_account_type": alert.get("Connector__account_type"),
                "sensitivity_level": alert.get("sensitivity_level"),
                "data_class_ids": [
                    data_class["id"] for data_class in alert.get("data_classes") or []
                ],
                "occurrences": alert.get("occurrences"),
                "total_violated_assets_count": alert.get(
                    "total_violated_assets_count",
                ),
                "created_at": alert.get("created_at"),
                "opened_at": alert.get("opened_at"),
                "last_modified": alert.get("last_modified"),
                "affected_data_store_id": (
                    alert["entity_id"] if entity_type == "STORE" else None
                ),
                "affected_aws_role_arn": (
                    cloud_unique_id
                    if entity_type == "IAM_ROLE"
                    and cloud_unique_id
                    and _AWS_ROLE_ARN_RE.match(cloud_unique_id)
                    else None
                ),
            },
        )
    return result


@timeit
def load_alerts(
    neo4j_session: neo4j.Session,
    data: Iterable[dict[str, Any]],
    tenant_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SentraAlertSchema(),
        data,
        lastupdated=update_tag,
        TENANT_ID=tenant_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(SentraAlertSchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    session: requests.Session,
    api_url: str,
    tenant_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    logger.info("Syncing Sentra alerts for organization %s", tenant_id)
    alerts = (alert for page in get(session, api_url) for alert in transform(page))
    load_alerts(neo4j_session, alerts, tenant_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)
