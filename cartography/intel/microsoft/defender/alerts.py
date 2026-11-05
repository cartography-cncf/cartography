import logging
from typing import Any

import neo4j
import requests
from azure.core.credentials import TokenCredential

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.microsoft.defender.client import get_collection
from cartography.intel.microsoft.defender.client import parse_timestamps
from cartography.models.microsoft.defender.alert import DefenderAlertSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)
ALERTS_URL = "https://graph.microsoft.com/v1.0/security/alerts_v2"
GRAPH_SCOPE = "https://graph.microsoft.com/.default"
PERMISSION = "Microsoft Graph SecurityAlert.Read.All"
# alerts_v2 documents only `eq` filters, so each unresolved status is queried separately.
UNRESOLVED_ALERT_STATUSES = ("new", "inProgress")


@timeit
def get_alerts(
    session: requests.Session, credential: TokenCredential
) -> list[dict[str, Any]]:
    alerts: dict[str, dict[str, Any]] = {}
    for status in UNRESOLVED_ALERT_STATUSES:
        for alert in get_collection(
            session,
            credential,
            ALERTS_URL,
            GRAPH_SCOPE,
            {
                "$top": 100,
                "$filter": (
                    "serviceSource eq 'microsoftDefenderForEndpoint' "
                    f"and status eq '{status}'"
                ),
            },
        ):
            # An alert whose status changes between queries can appear in both.
            alerts[alert["id"]] = alert
    return list(alerts.values())


def transform_alerts(
    alerts: list[dict[str, Any]], tenant_id: str
) -> list[dict[str, Any]]:
    result = []
    for alert in alerts:
        if alert.get("tenantId") not in (None, tenant_id):
            raise ValueError("Defender alert belongs to a different tenant")
        evidence = alert.get("evidence", [])
        if not isinstance(evidence, list) or any(
            not isinstance(item, dict) for item in evidence
        ):
            raise ValueError("Defender alert evidence is not a collection")
        result.append(
            {
                **alert,
                "id": f"{tenant_id}/{alert['id']}",
                "alert_id": alert["id"],
                "machine_ids": sorted(
                    {
                        f"{tenant_id}/{item['mdeDeviceId']}"
                        for item in evidence
                        if item.get("@odata.type")
                        == "#microsoft.graph.security.deviceEvidence"
                        and item.get("mdeDeviceId")
                    }
                ),
            },
        )
        parse_timestamps(result[-1], ("createdDateTime", "lastUpdateDateTime"))
    return result


@timeit
def load_alerts(
    neo4j_session: neo4j.Session,
    alerts: list[dict[str, Any]],
    tenant_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        DefenderAlertSchema(),
        alerts,
        lastupdated=update_tag,
        TENANT_ID=tenant_id,
    )


@timeit
def cleanup_alerts(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(DefenderAlertSchema(), common_job_parameters).run(
        neo4j_session
    )
