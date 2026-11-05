import logging
from typing import Any

import neo4j
from tencentcloud.common.credential import Credential

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.tencentcloud.util import call
from cartography.intel.tencentcloud.util import format_tags
from cartography.intel.tencentcloud.util import get_in_region
from cartography.intel.tencentcloud.util import paginate_offset
from cartography.models.tencentcloud.clb_load_balancer import (
    TencentCloudCLBLoadBalancerSchema,
)
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get(client: Any) -> list[dict[str, Any]]:
    """Return every load balancer in the region, each with its listener `Listeners`."""
    load_balancers = paginate_offset(
        client,
        "DescribeLoadBalancers",
        "LoadBalancerSet",
    )
    for load_balancer in load_balancers:
        response = call(
            client,
            "DescribeTargets",
            {"LoadBalancerId": load_balancer["LoadBalancerId"]},
        )
        load_balancer["Listeners"] = response.get("Listeners") or []
    return load_balancers


def _backend_instance_ids(listeners: list[dict[str, Any]]) -> list[str]:
    """Collect CVM instance IDs bound to any listener (layer 4) or rule (layer 7)."""
    instance_ids: set[str] = set()
    for listener in listeners:
        backends = list(listener.get("Targets") or [])
        for rule in listener.get("Rules") or []:
            backends.extend(rule.get("Targets") or [])
        for backend in backends:
            if backend.get("Type") == "CVM" and backend.get("InstanceId"):
                instance_ids.add(backend["InstanceId"])
    return sorted(instance_ids)


def transform(
    raw_load_balancers: list[dict[str, Any]],
    region: str,
) -> list[dict[str, Any]]:
    load_balancers = []
    for lb in raw_load_balancers:
        master_zone = lb.get("MasterZone") or {}
        load_balancers.append(
            {
                "id": lb["LoadBalancerId"],
                "name": lb.get("LoadBalancerName"),
                "region": region,
                "load_balancer_type": lb.get("LoadBalancerType"),
                "forward": lb.get("Forward"),
                "domain": lb.get("LoadBalancerDomain") or lb.get("Domain") or None,
                "vips": lb.get("LoadBalancerVips") or None,
                "ip_address": (lb.get("LoadBalancerVips") or [None])[0],
                "address_ipv6": lb.get("AddressIPv6") or None,
                "address_ip_version": lb.get("AddressIPVersion"),
                "status": lb.get("Status"),
                "isolation": lb.get("Isolation"),
                "project_id": (
                    str(lb["ProjectId"]) if lb.get("ProjectId") is not None else None
                ),
                "vpc_id": lb.get("VpcId") or None,
                "subnet_id": lb.get("SubnetId") or None,
                "security_group_ids": lb.get("SecureGroups") or [],
                "master_zone": master_zone.get("Zone"),
                "charge_type": lb.get("ChargeType"),
                "tags": format_tags(lb.get("Tags"), "TagKey", "TagValue"),
                "create_time": lb.get("CreateTime"),
                "backend_instance_ids": _backend_instance_ids(lb["Listeners"]),
            },
        )
    return load_balancers


@timeit
def load_load_balancers(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    logger.info(
        "Loading %d Tencent Cloud CLB load balancers for account %s.",
        len(data),
        account_id,
    )
    load(
        neo4j_session,
        TencentCloudCLBLoadBalancerSchema(),
        data,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(
        TencentCloudCLBLoadBalancerSchema(),
        common_job_parameters,
    ).run(neo4j_session)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    credential: Credential,
    account_id: str,
    regions: list[str],
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    load_balancers: list[dict[str, Any]] = []
    for region in regions:
        raw = get_in_region(credential, "clb", region, get)
        load_balancers.extend(transform(raw, region))
    load_load_balancers(neo4j_session, load_balancers, account_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)
