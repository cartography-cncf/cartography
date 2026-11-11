import logging
from typing import Any

import neo4j
from tencentcloud.common.credential import Credential

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.tencentcloud.util import format_tags
from cartography.intel.tencentcloud.util import get_in_region
from cartography.intel.tencentcloud.util import paginate_offset
from cartography.models.tencentcloud.cbs_disk import TencentCloudCBSDiskSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get(client: Any) -> list[dict[str, Any]]:
    return paginate_offset(client, "DescribeDisks", "DiskSet")


def transform(raw_disks: list[dict[str, Any]], region: str) -> list[dict[str, Any]]:
    disks = []
    for disk in raw_disks:
        placement = disk.get("Placement") or {}
        # Shared disks list every instance in InstanceIdList; other disks report their
        # single instance in InstanceId and leave InstanceIdList empty.
        attached_instance_ids = list(disk.get("InstanceIdList") or [])
        if disk.get("InstanceId") and disk["InstanceId"] not in attached_instance_ids:
            attached_instance_ids.append(disk["InstanceId"])
        disks.append(
            {
                "id": disk["DiskId"],
                "name": disk.get("DiskName"),
                "region": region,
                "zone": placement.get("Zone"),
                "project_id": (
                    str(placement["ProjectId"])
                    if placement.get("ProjectId") is not None
                    else None
                ),
                "disk_type": disk.get("DiskType"),
                "disk_usage": disk.get("DiskUsage"),
                "disk_size": disk.get("DiskSize"),
                "disk_state": disk.get("DiskState"),
                "attached": disk.get("Attached"),
                "encrypt": disk.get("Encrypt"),
                "kms_key_id": disk.get("KmsKeyId") or None,
                "shareable": disk.get("Shareable"),
                "portable": disk.get("Portable"),
                "delete_with_instance": disk.get("DeleteWithInstance"),
                "snapshot_count": disk.get("SnapshotCount"),
                "disk_charge_type": disk.get("DiskChargeType"),
                "tags": format_tags(disk.get("Tags")),
                "create_time": disk.get("CreateTime"),
                "attached_instance_ids": attached_instance_ids,
            },
        )
    return disks


@timeit
def load_disks(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    logger.info(
        "Loading %d Tencent Cloud CBS disks for account %s.",
        len(data),
        account_id,
    )
    load(
        neo4j_session,
        TencentCloudCBSDiskSchema(),
        data,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(TencentCloudCBSDiskSchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    credential: Credential,
    account_id: str,
    regions: list[str],
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    disks: list[dict[str, Any]] = []
    for region in regions:
        disks.extend(transform(get_in_region(credential, "cbs", region, get), region))
    load_disks(neo4j_session, disks, account_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)
