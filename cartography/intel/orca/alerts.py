import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.orca import api
from cartography.intel.orca.response import canonical_cve_ids
from cartography.intel.orca.response import empty_target_context
from cartography.intel.orca.response import field_value
from cartography.intel.orca.response import inventory_target_context
from cartography.intel.orca.response import optional_nonempty_string
from cartography.intel.orca.response import optional_number
from cartography.intel.orca.response import optional_string
from cartography.intel.orca.response import parse_datetime
from cartography.intel.orca.response import require_nonempty_string
from cartography.intel.orca.response import require_object
from cartography.intel.orca.response import unwrap_value
from cartography.models.orca import OrcaAlertSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

PAGE_SIZE = 100


def build_query() -> dict[str, Any]:
    # Related Inventory is optional target context. V1 does not load Inventory
    # nodes or create finding-to-asset relationships.
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


def _target_context_from_alert(
    raw_alert: dict[str, Any],
) -> dict[str, str | None]:
    inventory = unwrap_value(raw_alert.get("Inventory"))
    if inventory is None:
        return empty_target_context()
    if isinstance(inventory, list):
        # An alert is only safe to correlate when Orca supplies one unambiguous
        # inventory record. Never choose an arbitrary asset from a multi-value
        # response.
        if len(inventory) != 1:
            return empty_target_context()
        inventory = inventory[0]
    return inventory_target_context(inventory, "Orca Alert.Inventory")


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
    unresolved_targets = 0
    for raw_alert in raw_alerts:
        data = require_object(
            raw_alert.get("data"),
            "Orca Alert.data",
        )
        alert_id = require_nonempty_string(
            field_value(data, "AlertId"),
            "Orca AlertId",
        )

        target_context = _target_context_from_alert(raw_alert)
        if not any(
            target_context[key]
            for key in (
                "target_orca_inventory_id",
                "target_orca_asset_unique_id",
                "target_provider_id",
                "target_arn",
            )
        ):
            unresolved_targets += 1

        asset_data = _asset_data(data)
        if target_context["target_name"] is None:
            target_context["target_name"] = optional_nonempty_string(
                asset_data.get("asset_name"),
                "Orca Alert.AssetData.asset_name",
            )
        if target_context["target_type"] is None:
            target_context["target_type"] = optional_nonempty_string(
                asset_data.get("asset_type"),
                "Orca Alert.AssetData.asset_type",
            )
        alert_type = optional_string(
            field_value(data, "AlertType"),
            "Orca Alert.AlertType",
        )
        title = (
            optional_string(field_value(data, "Title"), "Orca Alert.Title")
            or alert_type
            or f"Orca alert {alert_id}"
        )
        transformed.append(
            {
                "id": f"orca:{organization_id}:{alert_id}",
                "orca_id": alert_id,
                "title": title,
                "details": optional_string(
                    field_value(data, "Details"),
                    "Orca Alert.Details",
                ),
                "severity": optional_string(
                    field_value(data, "Severity"),
                    "Orca Alert.Severity",
                ),
                "category": optional_string(
                    field_value(data, "Category"),
                    "Orca Alert.Category",
                ),
                "alert_type": alert_type,
                "orca_score": optional_number(
                    field_value(data, "OrcaScore"),
                    "Orca Alert.OrcaScore",
                ),
                "status": optional_string(
                    field_value(data, "Status"),
                    "Orca Alert.Status",
                ),
                "created_at": parse_datetime(
                    field_value(data, "CreatedAt"),
                    "Orca Alert.CreatedAt",
                ),
                "last_seen": parse_datetime(
                    field_value(data, "LastSeen"),
                    "Orca Alert.LastSeen",
                ),
                "console_url": optional_string(
                    field_value(data, "ConsoleUrlLink"),
                    "Orca Alert.ConsoleUrlLink",
                ),
                "cve_ids": canonical_cve_ids(
                    field_value(data, "CveIds"),
                ),
                **target_context,
            },
        )
    if unresolved_targets:
        logger.warning(
            "%d Orca alerts loaded without exact target identifiers.",
            unresolved_targets,
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
