import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.tenable.api import export_and_download
from cartography.models.tenable.assets import TenableAssetSchema
from cartography.models.tenable.cloud import TenableAssetAWSSchema
from cartography.models.tenable.cloud import TenableAssetAzureSchema
from cartography.models.tenable.cloud import TenableAssetGCPSchema
from cartography.models.tenable.network import TenableNetworkSchema
from cartography.models.tenable.sources import TenableAssetSourceSchema
from cartography.models.tenable.tags import TenableAssetTagSchema
from cartography.models.tenable.tenant import TenableTenantSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

_ASSET_EXPORT_PATH = "assets/v2/export"
_ASSET_RESULT_BASE = "assets/export"
_ASSET_EXPORT_PARAMS: dict[str, Any] = {"chunk_size": 1000}


@timeit
def get(
    session: requests.Session,
    base_url: str,
) -> list[dict[str, Any]]:
    logger.info("Initiating Tenable asset export from %s", base_url)
    return export_and_download(
        session,
        base_url,
        _ASSET_EXPORT_PATH,
        _ASSET_RESULT_BASE,
        _ASSET_EXPORT_PARAMS,
    )


def transform(raw_assets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    for asset in raw_assets:
        timestamps = asset.get("timestamps") or {}
        scan = asset.get("scan") or {}
        network = asset.get("network") or {}
        cloud = asset.get("cloud") or {}
        aws = cloud.get("aws") or {}
        azure = cloud.get("azure") or {}
        gcp = cloud.get("gcp") or {}
        ratings = asset.get("ratings") or {}
        fqdns = network.get("fqdns") or []

        result.append(
            {
                "id": asset["id"],
                # Core flags
                "has_agent": asset.get("has_agent"),
                "has_plugin_results": asset.get("has_plugin_results"),
                "is_licensed": asset.get("is_licensed"),
                "is_public": asset.get("is_public"),
                # Classification
                "types": asset.get("types") or [],
                "system_types": asset.get("system_types") or [],
                "operating_systems": asset.get("operating_systems") or [],
                "serial_number": asset.get("serial_number"),
                "tenable_agent_days_since_active": asset.get(
                    "tenable_agent_days_since_active"
                ),
                # Timestamps
                "created_at_timestamps": timestamps.get("created_at"),
                "updated_at_timestamps": timestamps.get("updated_at"),
                "first_seen_timestamps": timestamps.get("first_seen"),
                "last_seen_timestamps": timestamps.get("last_seen"),
                # Scan
                "first_scan_time": scan.get("first_scan_time"),
                "last_scan_time": scan.get("last_scan_time"),
                "last_authenticated_scan_date": scan.get(
                    "last_authenticated_scan_date"
                ),
                "last_licensed_scan_date": scan.get("last_licensed_scan_date"),
                "last_scan_id": scan.get("last_scan_id"),
                # Network — name detail in TenableNetwork
                "network_id": network.get("network_id"),
                "fqdn": fqdns[0] if fqdns else None,
                "ipv4s": network.get("ipv4s") or [],
                "ipv6s": network.get("ipv6s") or [],
                "fqdns": fqdns,
                "hostnames": network.get("hostnames") or [],
                "mac_addresses": network.get("mac_addresses") or [],
                # Cloud identifiers — detail in TenableAssetAWS / TenableAssetAzure / TenableAssetGCP
                "aws_ec2_instance_id": aws.get("ec2_instance_id"),
                "azure_vm_id": azure.get("vm_id"),
                "gcp_instance_id": gcp.get("instance_id"),
                # Ratings
                "acr_score": (ratings.get("acr") or {}).get("score"),
                "aes_score": (ratings.get("aes") or {}).get("score"),
            }
        )
    return result


def transform_networks(raw_assets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    result = []
    for asset in raw_assets:
        network = asset.get("network") or {}
        network_id = network.get("network_id")
        if network_id and network_id not in seen:
            seen.add(network_id)
            result.append(
                {
                    "id": network_id,
                    "name": network.get("network_name"),
                }
            )
    return result


def transform_sources(raw_assets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    for asset in raw_assets:
        asset_id = asset["id"]
        for source in asset.get("sources") or []:
            name = source.get("name") or ""
            result.append(
                {
                    "id": f"{asset_id}::{name}",
                    "name": name,
                    "source_first_seen": source.get("first_seen"),
                    "source_last_seen": source.get("last_seen"),
                    "asset_id": asset_id,
                }
            )
    return result


def transform_tags(raw_assets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    for asset in raw_assets:
        asset_id = asset["id"]
        for tag in asset.get("tags") or []:
            result.append(
                {
                    "id": tag["uuid"],
                    "tag_key": tag.get("key"),
                    "tag_value": tag.get("value"),
                    "added_by": tag.get("added_by"),
                    "added_at": tag.get("added_at"),
                    "asset_id": asset_id,
                }
            )
    return result


def transform_aws(raw_assets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    result = []
    for asset in raw_assets:
        aws = (asset.get("cloud") or {}).get("aws") or {}
        ec2_instance_id = aws.get("ec2_instance_id")
        if not ec2_instance_id or ec2_instance_id in seen:
            continue
        seen.add(ec2_instance_id)
        result.append(
            {
                "id": ec2_instance_id,
                "ec2_instance_ami_id": aws.get("ec2_instance_ami_id"),
                "owner_id": aws.get("owner_id"),
                "availability_zone": aws.get("availability_zone"),
                "region": aws.get("region"),
                "vpc_id": aws.get("vpc_id"),
                "subnet_id": aws.get("subnet_id"),
                "ec2_instance_type": aws.get("ec2_instance_type"),
                "ec2_instance_state_name": aws.get("ec2_instance_state_name"),
                "ec2_instance_group_name": aws.get("ec2_instance_group_name"),
                "ec2_name": aws.get("ec2_name"),
            }
        )
    return result


def transform_azure(raw_assets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    result = []
    for asset in raw_assets:
        azure = (asset.get("cloud") or {}).get("azure") or {}
        vm_id = azure.get("vm_id")
        if not vm_id or vm_id in seen:
            continue
        seen.add(vm_id)
        result.append(
            {
                "id": vm_id,
                "resource_id": azure.get("resource_id"),
            }
        )
    return result


def transform_gcp(raw_assets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    result = []
    for asset in raw_assets:
        gcp = (asset.get("cloud") or {}).get("gcp") or {}
        instance_id = gcp.get("instance_id")
        if not instance_id or instance_id in seen:
            continue
        seen.add(instance_id)
        result.append(
            {
                "id": instance_id,
                "project_id": gcp.get("project_id"),
                "zone": gcp.get("zone"),
            }
        )
    return result


@timeit
def load_assets(
    neo4j_session: neo4j.Session,
    assets: list[dict[str, Any]],
    networks: list[dict[str, Any]],
    aws_nodes: list[dict[str, Any]],
    azure_nodes: list[dict[str, Any]],
    gcp_nodes: list[dict[str, Any]],
    sources: list[dict[str, Any]],
    tags: list[dict[str, Any]],
    tenant_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        TenableTenantSchema(),
        [{"id": tenant_id}],
        lastupdated=update_tag,
    )
    # Networks and cloud nodes must be loaded before assets so outward
    # relationship targets exist when TenableAsset nodes are written.
    load(
        neo4j_session,
        TenableNetworkSchema(),
        networks,
        lastupdated=update_tag,
        TENABLE_TENANT_ID=tenant_id,
    )
    load(
        neo4j_session,
        TenableAssetAWSSchema(),
        aws_nodes,
        lastupdated=update_tag,
        TENABLE_TENANT_ID=tenant_id,
    )
    load(
        neo4j_session,
        TenableAssetAzureSchema(),
        azure_nodes,
        lastupdated=update_tag,
        TENABLE_TENANT_ID=tenant_id,
    )
    load(
        neo4j_session,
        TenableAssetGCPSchema(),
        gcp_nodes,
        lastupdated=update_tag,
        TENABLE_TENANT_ID=tenant_id,
    )
    load(
        neo4j_session,
        TenableAssetSchema(),
        assets,
        lastupdated=update_tag,
        TENABLE_TENANT_ID=tenant_id,
    )
    # Sources and tags carry asset_id for inward rels; assets must exist first.
    load(
        neo4j_session,
        TenableAssetSourceSchema(),
        sources,
        lastupdated=update_tag,
        TENABLE_TENANT_ID=tenant_id,
    )
    load(
        neo4j_session,
        TenableAssetTagSchema(),
        tags,
        lastupdated=update_tag,
        TENABLE_TENANT_ID=tenant_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(TenableAssetTagSchema(), common_job_parameters).run(
        neo4j_session
    )
    GraphJob.from_node_schema(TenableAssetSourceSchema(), common_job_parameters).run(
        neo4j_session
    )
    GraphJob.from_node_schema(TenableAssetAWSSchema(), common_job_parameters).run(
        neo4j_session
    )
    GraphJob.from_node_schema(TenableAssetAzureSchema(), common_job_parameters).run(
        neo4j_session
    )
    GraphJob.from_node_schema(TenableAssetGCPSchema(), common_job_parameters).run(
        neo4j_session
    )
    GraphJob.from_node_schema(TenableNetworkSchema(), common_job_parameters).run(
        neo4j_session
    )
    GraphJob.from_node_schema(TenableAssetSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    session: requests.Session,
    base_url: str,
    tenant_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    logger.info("Syncing Tenable assets for tenant %s", tenant_id)
    raw_assets = get(session, base_url)
    assets = transform(raw_assets)
    networks = transform_networks(raw_assets)
    aws_nodes = transform_aws(raw_assets)
    azure_nodes = transform_azure(raw_assets)
    gcp_nodes = transform_gcp(raw_assets)
    sources = transform_sources(raw_assets)
    tags = transform_tags(raw_assets)
    load_assets(
        neo4j_session,
        assets,
        networks,
        aws_nodes,
        azure_nodes,
        gcp_nodes,
        sources,
        tags,
        tenant_id,
        update_tag,
    )
    cleanup(neo4j_session, common_job_parameters)
