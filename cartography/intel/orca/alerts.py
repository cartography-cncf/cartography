import logging
import re
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.orca import api
from cartography.intel.orca.assets import make_asset_id
from cartography.models.orca import OrcaAlertSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

PAGE_SIZE = 100
_CVE_RE = re.compile(r"^CVE-\d{4}-\d{4,}$", re.IGNORECASE)


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


def _value(data: dict[str, Any], key: str) -> Any:
    value = data.get(key)
    if isinstance(value, dict) and "value" in value:
        return value.get("value")
    return value


def _required_value(data: dict[str, Any], key: str) -> Any:
    value = data[key]
    if isinstance(value, dict) and "value" in value:
        return value["value"]
    return value


def _normalize_cve_ids(*values: Any) -> list[str]:
    candidates: list[Any] = []
    for value in values:
        if isinstance(value, list):
            candidates.extend(value)
        elif value is not None:
            candidates.append(value)
    return sorted(
        {
            str(candidate).strip().upper()
            for candidate in candidates
            if _CVE_RE.fullmatch(str(candidate).strip())
        },
    )


def _inventory_from_alert(raw_alert: dict[str, Any], data: dict[str, Any]) -> Any:
    inventory = raw_alert.get("Inventory")
    if inventory is None:
        inventory = _value(data, "Inventory")
    if isinstance(inventory, dict) and "value" in inventory:
        inventory = inventory.get("value")
    if isinstance(inventory, list):
        # An alert is only safe to correlate when Orca supplies one unambiguous
        # inventory record. Never choose an arbitrary asset from a multi-value
        # response.
        return inventory[0] if len(inventory) == 1 else None
    return inventory


def transform(
    raw_alerts: list[dict[str, Any]],
    organization_id: str,
) -> list[dict[str, Any]]:
    transformed: list[dict[str, Any]] = []
    unresolved_assets = 0
    for raw_alert in raw_alerts:
        data = raw_alert.get("data") or raw_alert
        if not isinstance(data, dict):
            raise ValueError("Orca Alert.data must be an object")
        alert_id = _required_value(data, "AlertId")
        if not isinstance(alert_id, str) or not alert_id:
            raise ValueError("Orca AlertId must be a nonempty string")

        inventory = _inventory_from_alert(raw_alert, data)
        inventory_id = inventory.get("id") if isinstance(inventory, dict) else None
        asset_id = (
            make_asset_id(organization_id, inventory_id)
            if isinstance(inventory_id, str) and inventory_id
            else None
        )
        if asset_id is None:
            unresolved_assets += 1

        asset_data = _value(data, "AssetData") or {}
        if not isinstance(asset_data, dict):
            asset_data = {}
        alert_type = _value(data, "AlertType")
        title = _value(data, "Title") or alert_type or f"Orca alert {alert_id}"
        transformed.append(
            {
                "id": f"orca:{organization_id}:{alert_id}",
                "orca_id": alert_id,
                "title": title,
                "details": _value(data, "Details"),
                "severity": _value(data, "Severity"),
                "category": _value(data, "Category"),
                "alert_type": alert_type,
                "orca_score": _value(data, "OrcaScore"),
                "status": _value(data, "Status"),
                "created_at": _value(data, "CreatedAt"),
                "last_seen": _value(data, "LastSeen"),
                "console_url": _value(data, "ConsoleUrlLink"),
                "cve_ids": _normalize_cve_ids(
                    _value(data, "CveId"),
                    _value(data, "CveIds"),
                    _value(data, "CVEs"),
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
