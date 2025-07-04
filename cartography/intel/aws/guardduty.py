import logging
from typing import Any

import boto3
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.aws.guardduty.finding import AWSGuardDutyFindingSchema
from cartography.stats import get_stats_client
from cartography.util import aws_handle_regions
from cartography.util import merge_module_sync_metadata
from cartography.util import timeit

logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)


@timeit
@aws_handle_regions
def get_detectors(boto3_session: boto3.session.Session, region: str) -> list[str]:
    client = boto3_session.client("guardduty", region_name=region)
    resp = client.list_detectors()
    return resp.get("DetectorIds", [])


@timeit
@aws_handle_regions
def get_guardduty_findings(
    boto3_session: boto3.session.Session,
    region: str,
    detector_id: str,
) -> list[dict[str, Any]]:
    client = boto3_session.client("guardduty", region_name=region)
    ids = client.list_findings(DetectorId=detector_id).get("FindingIds", [])
    if not ids:
        return []
    resp = client.get_findings(DetectorId=detector_id, FindingIds=ids)
    return resp.get("Findings", [])


def transform_guardduty_findings(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    transformed: list[dict[str, Any]] = []
    for f in findings:
        item: dict[str, Any] = {
            "id": f["Id"],
            "arn": f.get("Arn"),
            "type": f.get("Type"),
            "severity": f.get("Severity"),
            "title": f.get("Title"),
            "description": f.get("Description"),
        }
        resource = f.get("Resource", {})
        item["resource_type"] = resource.get("ResourceType")
        if item["resource_type"] == "Instance":
            details = resource.get("InstanceDetails", {})
            item["resource_id"] = details.get("InstanceId")
        elif item["resource_type"] == "S3Bucket":
            buckets = resource.get("S3BucketDetails") or []
            if buckets:
                item["resource_id"] = buckets[0].get("Name")
        transformed.append(item)
    return transformed


@timeit
def load_guardduty_findings(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AWSGuardDutyFindingSchema(),
        data,
        Region=region,
        AWS_ID=current_aws_account_id,
        lastupdated=update_tag,
    )


@timeit
def cleanup_guardduty_findings(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(AWSGuardDutyFindingSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: list[str],
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    for region in regions:
        detectors = get_detectors(boto3_session, region)
        for detector_id in detectors:
            logger.info(
                f"Syncing GuardDuty findings for detector {detector_id} region {region} account {current_aws_account_id}."
            )
            findings = get_guardduty_findings(boto3_session, region, detector_id)
            transformed = transform_guardduty_findings(findings)
            load_guardduty_findings(
                neo4j_session,
                transformed,
                region,
                current_aws_account_id,
                update_tag,
            )

    cleanup_guardduty_findings(neo4j_session, common_job_parameters)

    merge_module_sync_metadata(
        neo4j_session,
        group_type="AWSAccount",
        group_id=current_aws_account_id,
        synced_type="AWSGuardDutyFinding",
        update_tag=update_tag,
        stat_handler=stat_handler,
    )
