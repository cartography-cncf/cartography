import logging
from typing import Any

import neo4j
from tencentcloud.common.credential import Credential

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.tencentcloud.util import format_tags
from cartography.intel.tencentcloud.util import get_in_region
from cartography.intel.tencentcloud.util import paginate_offset
from cartography.models.tencentcloud.cvm_instance import TencentCloudCVMInstanceSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get(client: Any) -> list[dict[str, Any]]:
    return paginate_offset(client, "DescribeInstances", "InstanceSet")


def transform(
    raw_instances: list[dict[str, Any]],
    region: str,
    account_id: str,
) -> list[dict[str, Any]]:
    instances = []
    for instance in raw_instances:
        placement = instance.get("Placement") or {}
        vpc = instance.get("VirtualPrivateCloud") or {}
        internet = instance.get("InternetAccessible") or {}
        login = instance.get("LoginSettings") or {}
        cam_role_name = instance.get("CamRoleName") or None
        instances.append(
            {
                "id": instance["InstanceId"],
                "uuid": instance.get("Uuid"),
                "name": instance.get("InstanceName"),
                "hostname": instance.get("HostName") or None,
                "region": region,
                "zone": placement.get("Zone"),
                "project_id": (
                    str(placement["ProjectId"])
                    if placement.get("ProjectId") is not None
                    else None
                ),
                "instance_type": instance.get("InstanceType"),
                "cpu": instance.get("CPU"),
                "memory": instance.get("Memory"),
                "state": instance.get("InstanceState"),
                "restrict_state": instance.get("RestrictState"),
                "image_id": instance.get("ImageId"),
                "os_name": instance.get("OsName"),
                "private_ip_addresses": instance.get("PrivateIpAddresses") or None,
                "public_ip_addresses": instance.get("PublicIpAddresses") or None,
                "private_ip_address": (instance.get("PrivateIpAddresses") or [None])[0],
                "public_ip_address": (instance.get("PublicIpAddresses") or [None])[0],
                "ipv6_addresses": instance.get("IPv6Addresses") or None,
                "internet_max_bandwidth_out": internet.get("InternetMaxBandwidthOut"),
                "vpc_id": vpc.get("VpcId") or None,
                "subnet_id": vpc.get("SubnetId") or None,
                "security_group_ids": instance.get("SecurityGroupIds") or [],
                "cam_role_name": cam_role_name,
                # CAM role ARNs follow a fixed format, so the bound role can be matched
                # without knowing its role ID.
                "cam_role_arn": (
                    f"qcs::cam::uin/{account_id}:roleName/{cam_role_name}"
                    if cam_role_name
                    else None
                ),
                "key_ids": login.get("KeyIds") or None,
                "disable_api_termination": instance.get("DisableApiTermination"),
                "instance_charge_type": instance.get("InstanceChargeType"),
                "tags": format_tags(instance.get("Tags")),
                "created_time": instance.get("CreatedTime"),
                "expired_time": instance.get("ExpiredTime"),
            },
        )
    return instances


@timeit
def load_instances(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    logger.info(
        "Loading %d Tencent Cloud CVM instances for account %s.",
        len(data),
        account_id,
    )
    load(
        neo4j_session,
        TencentCloudCVMInstanceSchema(),
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
        TencentCloudCVMInstanceSchema(),
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
    instances: list[dict[str, Any]] = []
    for region in regions:
        raw = get_in_region(credential, "cvm", region, get)
        instances.extend(transform(raw, region, account_id))
    load_instances(neo4j_session, instances, account_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)
