from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.orca import api
from cartography.intel.orca.response import field_value
from cartography.intel.orca.response import optional_nonempty_string
from cartography.intel.orca.response import parse_datetime
from cartography.intel.orca.response import require_nonempty_string
from cartography.intel.orca.response import require_object
from cartography.models.orca import OrcaAssetSchema
from cartography.util import timeit

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


def _normalize_tags(value: Any) -> list[str]:
    if isinstance(value, dict):
        return [f"{key}={value[key]}" for key in sorted(value)]
    if value is None:
        return []
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return [item.strip() for item in value if item.strip()]
    raise ValueError("Orca Inventory.Tags must be an object or string list")


def _normalize_zones(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [require_nonempty_string(value, "Orca Inventory.Zones")]
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return [require_nonempty_string(item, "Orca Inventory.Zones") for item in value]
    raise ValueError("Orca Inventory.Zones must be a string or string list")


def transform(
    raw_assets: list[dict[str, Any]],
    organization_id: str,
) -> list[dict[str, Any]]:
    transformed: list[dict[str, Any]] = []
    seen_asset_unique_ids: set[str] = set()
    for raw_asset in raw_assets:
        orca_id = require_nonempty_string(raw_asset["id"], "Orca Inventory.id")
        data = require_object(raw_asset.get("data", {}), "Orca Inventory.data")
        asset_unique_id = raw_asset.get("asset_unique_id")
        if asset_unique_id is None:
            asset_unique_id = field_value(data, "AssetUniqueId")
        asset_unique_id = optional_nonempty_string(
            asset_unique_id,
            "Orca Inventory.asset_unique_id",
        )
        if asset_unique_id is not None:
            if asset_unique_id in seen_asset_unique_ids:
                raise ValueError(
                    "Orca Inventory response contained duplicate asset_unique_id values",
                )
            seen_asset_unique_ids.add(asset_unique_id)
        last_seen = raw_asset.get("last_seen")
        if last_seen is None:
            last_seen = field_value(data, "LastSeen")
        transformed.append(
            {
                "id": make_asset_id(organization_id, orca_id),
                "orca_id": orca_id,
                "asset_unique_id": asset_unique_id,
                "group_unique_id": raw_asset.get("group_unique_id")
                or field_value(data, "GroupUniqueId"),
                "cluster_unique_id": raw_asset.get("cluster_unique_id")
                or field_value(data, "cluster_unique_id", "ClusterUniqueId"),
                "name": raw_asset.get("name") or field_value(data, "Name"),
                "asset_type": raw_asset.get("type") or field_value(data, "Type"),
                "category": field_value(data, "NewCategory", "Category"),
                "subcategory": field_value(
                    data,
                    "NewSubCategory",
                    "SubCategory",
                ),
                "cloud_provider": field_value(
                    data,
                    "CloudProvider",
                    "CloudPlatform",
                ),
                "cloud_account_id": field_value(
                    data,
                    "CloudAccountId",
                    "AccountId",
                    "SubscriptionId",
                    "ProjectId",
                ),
                "cloud_account_name": field_value(
                    data,
                    "CloudAccountName",
                    "AccountName",
                ),
                "region": field_value(data, "Region"),
                "zones": _normalize_zones(
                    field_value(data, "Zones", "AvailabilityZones"),
                ),
                "provider_id": field_value(
                    data,
                    "UiUniqueField",
                    "ProviderId",
                    "ResourceId",
                ),
                "arn": field_value(data, "Arn"),
                "state": field_value(data, "State"),
                "exposure": field_value(data, "Exposure"),
                "risk_level": field_value(data, "RiskLevel"),
                "orca_score": field_value(data, "OrcaScore"),
                "console_url": field_value(data, "ConsoleUrlLink"),
                "tags": _normalize_tags(field_value(data, "Tags")),
                "first_seen": parse_datetime(
                    field_value(data, "FirstSeen"),
                    "Orca Inventory.FirstSeen",
                ),
                "last_seen": parse_datetime(
                    last_seen,
                    "Orca Inventory.LastSeen",
                ),
                "creation_time": parse_datetime(
                    field_value(data, "CreationTime"),
                    "Orca Inventory.CreationTime",
                ),
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
