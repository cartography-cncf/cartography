import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.orca import api
from cartography.models.orca import OrcaAssetSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

PAGE_SIZE = 100


def build_query() -> dict[str, Any]:
    return {
        "query": {
            "models": ["Inventory"],
            "type": "object_set",
            "with": {"operator": "and", "type": "operation", "values": []},
        },
    }


def make_asset_id(organization_id: str, inventory_id: str) -> str:
    return f"orca:{organization_id}:{inventory_id}"


def _value(data: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key not in data:
            continue
        value = data[key]
        if isinstance(value, dict) and "value" in value:
            return value.get("value")
        return value
    return None


def _normalize_tags(value: Any) -> list[str]:
    if isinstance(value, dict):
        return [f"{key}={value[key]}" for key in sorted(value)]
    if isinstance(value, list):
        return [str(item) for item in value]
    if value is None:
        return []
    return [str(value)]


def transform(
    raw_assets: list[dict[str, Any]],
    organization_id: str,
) -> list[dict[str, Any]]:
    transformed: list[dict[str, Any]] = []
    seen_asset_unique_ids: set[str] = set()
    for raw_asset in raw_assets:
        orca_id = raw_asset["id"]
        if not isinstance(orca_id, str) or not orca_id:
            raise ValueError("Orca Inventory.id must be a nonempty string")
        data = raw_asset.get("data") or {}
        if not isinstance(data, dict):
            raise ValueError("Orca Inventory.data must be an object")
        asset_unique_id = raw_asset.get("asset_unique_id") or _value(
            data,
            "AssetUniqueId",
        )
        if asset_unique_id is not None:
            if not isinstance(asset_unique_id, str) or not asset_unique_id.strip():
                raise ValueError(
                    "Orca Inventory.asset_unique_id must be a nonempty string",
                )
            asset_unique_id = asset_unique_id.strip()
            if asset_unique_id in seen_asset_unique_ids:
                raise ValueError(
                    "Orca Inventory response contained duplicate asset_unique_id values",
                )
            seen_asset_unique_ids.add(asset_unique_id)
        zones = _value(data, "Zones", "AvailabilityZones")
        transformed.append(
            {
                "id": make_asset_id(organization_id, orca_id),
                "orca_id": orca_id,
                "asset_unique_id": asset_unique_id,
                "group_unique_id": raw_asset.get("group_unique_id")
                or _value(data, "GroupUniqueId"),
                "cluster_unique_id": raw_asset.get("cluster_unique_id")
                or _value(data, "cluster_unique_id", "ClusterUniqueId"),
                "name": raw_asset.get("name") or _value(data, "Name"),
                "asset_type": raw_asset.get("type") or _value(data, "Type"),
                "category": _value(data, "NewCategory", "Category"),
                "subcategory": _value(data, "NewSubCategory", "SubCategory"),
                "cloud_provider": _value(data, "CloudProvider", "CloudPlatform"),
                "cloud_account_id": _value(
                    data,
                    "CloudAccountId",
                    "AccountId",
                    "SubscriptionId",
                    "ProjectId",
                ),
                "cloud_account_name": _value(data, "CloudAccountName", "AccountName"),
                "region": _value(data, "Region"),
                "zones": (
                    zones if isinstance(zones, list) else ([zones] if zones else [])
                ),
                "provider_id": _value(
                    data,
                    "UiUniqueField",
                    "ProviderId",
                    "ResourceId",
                ),
                "arn": _value(data, "Arn"),
                "state": _value(data, "State"),
                "exposure": _value(data, "Exposure"),
                "risk_level": _value(data, "RiskLevel"),
                "orca_score": _value(data, "OrcaScore"),
                "console_url": _value(data, "ConsoleUrlLink"),
                "tags": _normalize_tags(_value(data, "Tags")),
                "first_seen": _value(data, "FirstSeen"),
                "last_seen": raw_asset.get("last_seen") or _value(data, "LastSeen"),
                "creation_time": _value(data, "CreationTime"),
            },
        )
    return transformed


def load_assets(
    neo4j_session: neo4j.Session,
    assets: list[dict[str, Any]],
    organization_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        OrcaAssetSchema(),
        assets,
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
    seen_asset_unique_ids: set[str] = set()
    for page in api.iter_serving_layer_pages(
        session,
        api_endpoint,
        build_query(),
        page_size=PAGE_SIZE,
        result_name="assets",
    ):
        assets = transform(page, organization_id)
        page_ids = {asset["id"] for asset in assets}
        if len(page_ids) != len(assets) or page_ids & seen_ids:
            raise RuntimeError("Orca assets response contained duplicate identities")
        page_asset_unique_ids = {
            asset["asset_unique_id"]
            for asset in assets
            if asset["asset_unique_id"] is not None
        }
        if page_asset_unique_ids & seen_asset_unique_ids:
            raise RuntimeError(
                "Orca assets response contained duplicate asset_unique_id values",
            )
        seen_ids.update(page_ids)
        seen_asset_unique_ids.update(page_asset_unique_ids)
        load_assets(neo4j_session, assets, organization_id, update_tag)


def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(OrcaAssetSchema(), common_job_parameters).run(
        neo4j_session,
    )
