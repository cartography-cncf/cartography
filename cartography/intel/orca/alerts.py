import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.orca import api
from cartography.intel.orca.assets import make_asset_id
from cartography.intel.orca.response import canonical_cve_ids
from cartography.intel.orca.response import field_value
from cartography.intel.orca.response import parse_datetime
from cartography.intel.orca.response import require_nonempty_string
from cartography.intel.orca.response import require_object
from cartography.intel.orca.response import unwrap_value
from cartography.models.orca import OrcaAlertSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

PAGE_SIZE = 100


def build_query() -> dict[str, Any]:
    # Request the related Inventory graph. AFFECTS is created only when the
    # response actually includes one unambiguous Inventory.id.
    return {
        "query": {
            "models": ["Alert"],
            "type": "object_set",
            "with": {"operator": "and", "type": "operation", "values": []},
        },
        "order_by[]": ["CreatedAt"],
        "additional_models[]": ["Inventory"],
        "full_graph_fetch": {"enabled": True},
        "max_tier": 2,
    }


def _inventory_id_from_alert(
    raw_alert: dict[str, Any],
    data: dict[str, Any],
) -> str | None:
    inventory = raw_alert.get("Inventory")
    if inventory is None:
        inventory = field_value(data, "Inventory")
    inventory = unwrap_value(inventory)
    if inventory is None:
        return None
    if isinstance(inventory, list):
        # An alert is only safe to correlate when Orca supplies one unambiguous
        # inventory record. Never choose an arbitrary asset from a multi-value
        # response.
        if len(inventory) != 1:
            return None
        inventory = inventory[0]
    inventory = require_object(inventory, "Orca Alert.Inventory")
    inventory_id = inventory.get("id")
    if inventory_id is None:
        return None
    return require_nonempty_string(inventory_id, "Orca Alert.Inventory.id")


def _asset_data(data: dict[str, Any]) -> dict[str, Any]:
    asset_data = field_value(data, "AssetData")
    if asset_data is None:
        return {}
    return require_object(asset_data, "Orca Alert.AssetData")


def transform(
    raw_alerts: list[dict[str, Any]],
    organization_id: str,
) -> list[dict[str, Any]]:
    transformed: list[dict[str, Any]] = []
    unresolved_assets = 0
    for raw_alert in raw_alerts:
        data = require_object(
            raw_alert["data"] if "data" in raw_alert else raw_alert,
            "Orca Alert.data",
        )
        alert_id = require_nonempty_string(
            unwrap_value(data["AlertId"]),
            "Orca AlertId",
        )

        inventory_id = _inventory_id_from_alert(raw_alert, data)
        asset_id = (
            make_asset_id(organization_id, inventory_id)
            if inventory_id is not None
            else None
        )
        if asset_id is None:
            unresolved_assets += 1

        asset_data = _asset_data(data)
        alert_type = field_value(data, "AlertType")
        title = field_value(data, "Title") or alert_type or f"Orca alert {alert_id}"
        transformed.append(
            {
                "id": f"orca:{organization_id}:{alert_id}",
                "orca_id": alert_id,
                "title": title,
                "details": field_value(data, "Details"),
                "severity": field_value(data, "Severity"),
                "category": field_value(data, "Category"),
                "alert_type": alert_type,
                "orca_score": field_value(data, "OrcaScore"),
                "status": field_value(data, "Status"),
                "created_at": parse_datetime(
                    field_value(data, "CreatedAt"),
                    "Orca Alert.CreatedAt",
                ),
                "last_seen": parse_datetime(
                    field_value(data, "LastSeen"),
                    "Orca Alert.LastSeen",
                ),
                "console_url": field_value(data, "ConsoleUrlLink"),
                "cve_ids": canonical_cve_ids(
                    field_value(data, "CveId"),
                    field_value(data, "CveIds"),
                    field_value(data, "CVEs"),
                ),
                "asset_id": asset_id,
                "asset_name": asset_data.get("asset_name"),
                "asset_type": asset_data.get("asset_type"),
            },
        )
    if unresolved_assets:
        logger.warning(
            "%d Orca alerts lacked one unambiguous Inventory.id and were loaded "
            "without AFFECTS edges.",
            unresolved_assets,
        )
    return transformed


def load_alerts(
    neo4j_session: neo4j.Session,
    alerts: list[dict[str, Any]],
    organization_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        OrcaAlertSchema(),
        alerts,
        lastupdated=update_tag,
        ORCA_ORGANIZATION_ID=organization_id,
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    session: requests.Session,
    api_endpoint: str,
    organization_id: str,
    update_tag: int,
) -> None:
    seen_ids: set[str] = set()
    for page in api.iter_serving_layer_pages(
        session,
        api_endpoint,
        build_query(),
        page_size=PAGE_SIZE,
        result_name="alerts",
    ):
        alerts = transform(page, organization_id)
        page_ids = {alert["id"] for alert in alerts}
        if len(page_ids) != len(alerts) or page_ids & seen_ids:
            raise RuntimeError("Orca alerts response contained duplicate identities")
        seen_ids.update(page_ids)
        load_alerts(neo4j_session, alerts, organization_id, update_tag)


def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(OrcaAlertSchema(), common_job_parameters).run(
        neo4j_session,
    )
