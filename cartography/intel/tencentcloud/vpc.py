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
from cartography.models.tencentcloud.security_group import (
    TencentCloudSecurityGroupSchema,
)
from cartography.models.tencentcloud.security_group_rule import (
    TencentCloudSecurityGroupRuleSchema,
)
from cartography.models.tencentcloud.subnet import TencentCloudSubnetSchema
from cartography.models.tencentcloud.vpc import TencentCloudVPCSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# GET
# ---------------------------------------------------------------------------


@timeit
def get_vpcs(client: Any) -> list[dict[str, Any]]:
    return paginate_offset(client, "DescribeVpcs", "VpcSet", string_paging=True)


@timeit
def get_subnets(client: Any) -> list[dict[str, Any]]:
    return paginate_offset(client, "DescribeSubnets", "SubnetSet", string_paging=True)


@timeit
def get_security_groups(client: Any) -> list[dict[str, Any]]:
    """Return every security group in the region, each with its `SecurityGroupPolicySet`."""
    groups = paginate_offset(
        client,
        "DescribeSecurityGroups",
        "SecurityGroupSet",
        string_paging=True,
    )
    for group in groups:
        response = call(
            client,
            "DescribeSecurityGroupPolicies",
            {"SecurityGroupId": group["SecurityGroupId"]},
        )
        group["SecurityGroupPolicySet"] = response["SecurityGroupPolicySet"]
    return groups


# ---------------------------------------------------------------------------
# TRANSFORM
# ---------------------------------------------------------------------------


def transform_vpcs(raw_vpcs: list[dict[str, Any]], region: str) -> list[dict[str, Any]]:
    return [
        {
            "id": vpc["VpcId"],
            "name": vpc.get("VpcName"),
            "region": region,
            "cidr_block": vpc.get("CidrBlock") or None,
            "assistant_cidr_blocks": [
                cidr["CidrBlock"] for cidr in vpc.get("AssistantCidrSet") or []
            ]
            or None,
            "ipv6_cidr_block": vpc.get("Ipv6CidrBlock") or None,
            "is_default": vpc.get("IsDefault"),
            "enable_multicast": vpc.get("EnableMulticast"),
            "dns_servers": vpc.get("DnsServerSet") or None,
            "domain_name": vpc.get("DomainName") or None,
            "tags": format_tags(vpc.get("TagSet")),
            "created_time": vpc.get("CreatedTime"),
        }
        for vpc in raw_vpcs
    ]


def transform_subnets(
    raw_subnets: list[dict[str, Any]],
    region: str,
) -> list[dict[str, Any]]:
    return [
        {
            "id": subnet["SubnetId"],
            "name": subnet.get("SubnetName"),
            "region": region,
            "zone": subnet.get("Zone"),
            "vpc_id": subnet["VpcId"],
            "cidr_block": subnet.get("CidrBlock") or None,
            "ipv6_cidr_block": subnet.get("Ipv6CidrBlock") or None,
            "is_default": subnet.get("IsDefault"),
            "route_table_id": subnet.get("RouteTableId") or None,
            "network_acl_id": subnet.get("NetworkAclId") or None,
            "available_ip_address_count": subnet.get("AvailableIpAddressCount"),
            "total_ip_address_count": subnet.get("TotalIpAddressCount"),
            "tags": format_tags(subnet.get("TagSet")),
            "created_time": subnet.get("CreatedTime"),
        }
        for subnet in raw_subnets
    ]


def transform_security_groups(
    raw_groups: list[dict[str, Any]],
    region: str,
) -> list[dict[str, Any]]:
    return [
        {
            "id": group["SecurityGroupId"],
            "name": group.get("SecurityGroupName"),
            "description": group.get("SecurityGroupDesc") or None,
            "region": region,
            "project_id": (
                str(group["ProjectId"]) if group.get("ProjectId") is not None else None
            ),
            "is_default": group.get("IsDefault"),
            "tags": format_tags(group.get("TagSet")),
            "created_time": group.get("CreatedTime"),
            "update_time": group.get("UpdateTime"),
        }
        for group in raw_groups
    ]


def parse_port_range(port: str | None) -> tuple[int | None, int | None]:
    """Map a Tencent Cloud port expression to an inclusive (from, to) range.

    `all` covers every port, `80` and `8000-8010` map directly. A discrete list such as
    `80,443` cannot be expressed as one range and maps to (None, None).
    """
    if not port:
        return None, None
    port = port.strip()
    if port.upper() == "ALL":
        return 0, 65535
    if "," in port:
        return None, None
    if "-" in port:
        low, high = port.split("-", 1)
        return int(low), int(high)
    return int(port), int(port)


def transform_security_group_rules(
    raw_groups: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rules = []
    for group in raw_groups:
        group_id = group["SecurityGroupId"]
        policy_set = group["SecurityGroupPolicySet"]
        for direction, raw_rules in (
            ("ingress", policy_set.get("Ingress") or []),
            ("egress", policy_set.get("Egress") or []),
        ):
            for raw in raw_rules:
                policy_index = raw["PolicyIndex"]
                protocol = raw.get("Protocol") or None
                port = raw.get("Port") or None
                fromport, toport = parse_port_range(port)
                if protocol and protocol.upper() == "ALL" and port is None:
                    fromport, toport = 0, 65535
                address_template = raw.get("AddressTemplate") or {}
                service_template = raw.get("ServiceTemplate") or {}
                rules.append(
                    {
                        "id": f"{group_id}/{direction}/{policy_index}",
                        "security_group_id": group_id,
                        "direction": direction,
                        "policy_index": policy_index,
                        "action": raw.get("Action"),
                        "protocol": protocol,
                        "port": port,
                        "fromport": fromport,
                        "toport": toport,
                        "cidr_block": raw.get("CidrBlock") or None,
                        "ipv6_cidr_block": raw.get("Ipv6CidrBlock") or None,
                        "source_security_group_id": raw.get("SecurityGroupId") or None,
                        "address_template_id": address_template.get("AddressId")
                        or address_template.get("AddressGroupId")
                        or None,
                        "service_template_id": service_template.get("ServiceId")
                        or service_template.get("ServiceGroupId")
                        or None,
                        "description": raw.get("PolicyDescription") or None,
                        "modify_time": raw.get("ModifyTime"),
                    },
                )
    return rules


# ---------------------------------------------------------------------------
# LOAD / CLEANUP
# ---------------------------------------------------------------------------


def _load(
    neo4j_session: neo4j.Session,
    schema: Any,
    data: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    logger.info(
        "Loading %d %s nodes for Tencent Cloud account %s.",
        len(data),
        schema.label,
        account_id,
    )
    load(
        neo4j_session,
        schema,
        data,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    for schema in (
        TencentCloudSecurityGroupRuleSchema(),
        TencentCloudSecurityGroupSchema(),
        TencentCloudSubnetSchema(),
        TencentCloudVPCSchema(),
    ):
        GraphJob.from_node_schema(schema, common_job_parameters).run(neo4j_session)


# ---------------------------------------------------------------------------
# SYNC
# ---------------------------------------------------------------------------


@timeit
def sync(
    neo4j_session: neo4j.Session,
    credential: Credential,
    account_id: str,
    regions: list[str],
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    """Sync VPCs, subnets, security groups, and security group rules in every region."""
    vpcs: list[dict[str, Any]] = []
    subnets: list[dict[str, Any]] = []
    raw_groups: list[dict[str, Any]] = []
    security_groups: list[dict[str, Any]] = []
    for region in regions:
        vpcs.extend(
            transform_vpcs(get_in_region(credential, "vpc", region, get_vpcs), region),
        )
        subnets.extend(
            transform_subnets(
                get_in_region(credential, "vpc", region, get_subnets),
                region,
            ),
        )
        region_groups = get_in_region(credential, "vpc", region, get_security_groups)
        raw_groups.extend(region_groups)
        security_groups.extend(transform_security_groups(region_groups, region))

    _load(neo4j_session, TencentCloudVPCSchema(), vpcs, account_id, update_tag)
    _load(neo4j_session, TencentCloudSubnetSchema(), subnets, account_id, update_tag)
    _load(
        neo4j_session,
        TencentCloudSecurityGroupSchema(),
        security_groups,
        account_id,
        update_tag,
    )
    _load(
        neo4j_session,
        TencentCloudSecurityGroupRuleSchema(),
        transform_security_group_rules(raw_groups),
        account_id,
        update_tag,
    )
    cleanup(neo4j_session, common_job_parameters)
