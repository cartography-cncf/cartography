import logging
from typing import Any
from typing import Dict
from typing import List

import boto3
import boto3.session
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.aws.guardduty.findings import GuardDutyFindingSchema
from cartography.models.aws.guardduty.detector import GuardDutyDetectorSchema
from cartography.stats import get_stats_client
from cartography.util import aws_handle_regions
from cartography.util import aws_paginate
from cartography.util import merge_module_sync_metadata
from cartography.util import timeit

logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)


def _get_severity_range_for_threshold(
    severity_threshold: str | None,
) -> List[str] | None:
    """
    Convert severity threshold string to GuardDuty numeric severity range.

    GuardDuty severity mappings:
    - LOW: 1.0-3.9
    - MEDIUM: 4.0-6.9
    - HIGH: 7.0-8.9
    - CRITICAL: 9.0-10.0

    :param severity_threshold: Severity threshold (LOW, MEDIUM, HIGH, CRITICAL)
    :return: List of numeric severity ranges to include, or None for no filtering
    """
    if not severity_threshold:
        return None

    threshold_upper = severity_threshold.upper().strip()

    # Map threshold to numeric ranges - include threshold level and above
    if threshold_upper == "LOW":
        return ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]  # All severities
    elif threshold_upper == "MEDIUM":
        return ["4", "5", "6", "7", "8", "9", "10"]  # MEDIUM and above
    elif threshold_upper == "HIGH":
        return ["7", "8", "9", "10"]  # HIGH and CRITICAL only
    elif threshold_upper == "CRITICAL":
        return ["9", "10"]  # CRITICAL only
    else:
        return None


@aws_handle_regions
def get_detectors(
    boto3_session: boto3.session.Session,
    region: str,
) -> List[str]:
    """
    Get GuardDuty detector IDs for all detectors in a region.
    """
    client = boto3_session.client("guardduty", region_name=region)

    # Get all detector IDs in this region
    detectors_response = client.list_detectors()
    detector_ids = detectors_response.get("DetectorIds", [])

    if not detector_ids:
        logger.info(f"No GuardDuty detectors found in region {region}")
        return []

    logger.info(f"Found {len(detector_ids)} GuardDuty detectors in region {region}")
    return detector_ids


@aws_handle_regions
@timeit
def get_findings(
    boto3_session: boto3.session.Session,
    region: str,
    detector_id: str,
    severity_threshold: str | None = None,
) -> List[Dict[str, Any]]:
    """
    Get GuardDuty findings for a specific detector.
    Only fetches unarchived findings to avoid including closed/resolved findings.
    Optionally filters by severity threshold.
    """
    client = boto3_session.client("guardduty", region_name=region)

    # Build FindingCriteria - always exclude archived findings
    criteria = {"service.archived": {"Equals": ["false"]}}

    # Add severity filtering if threshold is provided
    severity_range = _get_severity_range_for_threshold(severity_threshold)
    if severity_range:
        min_severity = min(
            float(s) for s in severity_range
        )  # get min severity from range
        # I chose to ignore the type error here  because the AWS API has fields that require different types
        criteria["severity"] = {"GreaterThanOrEqual": int(min_severity)}  # type: ignore

    # Get all finding IDs for this detector with filtering
    finding_ids = list(
        aws_paginate(
            client,
            "list_findings",
            "FindingIds",
            DetectorId=detector_id,
            FindingCriteria={"Criterion": criteria},
        )
    )

    if not finding_ids:
        logger.info(f"No findings found for detector {detector_id} in region {region}")
        return []

    findings_data = []

    # Process findings in batches (GuardDuty API limit is 50)
    batch_size = 50
    for i in range(0, len(finding_ids), batch_size):
        batch_ids = finding_ids[i : i + batch_size]

        findings_response = client.get_findings(
            DetectorId=detector_id, FindingIds=batch_ids
        )

        findings_batch = findings_response.get("Findings", [])
        findings_data.extend(findings_batch)

    logger.info(
        f"Retrieved {len(findings_data)} findings for detector {detector_id} in region {region}"
    )
    return findings_data


def transform_findings(findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Transform GuardDuty findings from API response to schema format."""
    transformed: List[Dict[str, Any]] = []
    for f in findings:
        item: Dict[str, Any] = {
            "id": f["Id"],
            "arn": f.get("Arn"),
            "type": f.get("Type"),
            "severity": f.get("Severity"),
            "title": f.get("Title"),
            "description": f.get("Description"),
            "confidence": f.get("Confidence"),
            "eventfirstseen": f.get("EventFirstSeen"),
            "eventlastseen": f.get("EventLastSeen"),
            "accountid": f.get("AccountId"),
            "region": f.get("Region"),
            "detectorid": f.get("DetectorId"),
            "archived": f.get("Archived"),
        }

        # Handle nested resource information
        resource = f.get("Resource", {})
        item["resource_type"] = resource.get("ResourceType")

        # Extract resource ID based on resource type
        if item["resource_type"] == "Instance":
            details = resource.get("InstanceDetails", {})
            item["resource_id"] = details.get("InstanceId")
        elif item["resource_type"] == "S3Bucket":
            buckets = resource.get("S3BucketDetails") or []
            if buckets:
                item["resource_id"] = buckets[0].get("Name")
        else:
            item["resource_id"] = None

        transformed.append(item)

    return transformed


@timeit
def load_guardduty_findings(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    region: str,
    aws_account_id: str,
    update_tag: int,
) -> None:
    """
    Load GuardDuty findings information into the graph.
    """
    logger.info(
        f"Loading {len(data)} GuardDuty findings for region {region} into graph."
    )

    load(
        neo4j_session,
        GuardDutyFindingSchema(),
        data,
        lastupdated=update_tag,
        Region=region,
        AWS_ID=aws_account_id,
    )


@aws_handle_regions
@timeit
def get_detector_details(
    boto3_session: boto3.session.Session,
    region: str,
    detector_ids: List[str],
) -> List[Dict[str, Any]]:
    """
    Get detailed information about GuardDuty detectors.
    """
    if not detector_ids:
        return []

    client = boto3_session.client("guardduty", region_name=region)
    detector_details = []

    for detector_id in detector_ids:
        try:
            response = client.get_detector(DetectorId=detector_id)
            detector_details.append({"DetectorId": detector_id, **response})
        except Exception as e:
            logger.warning(f"Failed to get detector details for {detector_id}: {e}")
            continue

    return detector_details


def transform_detector_details(detector_details: List[Dict[str, Any]], region: str) -> List[Dict[str, Any]]:
    """
    Transform GuardDuty detector details from API response to schema format.
    """
    transformed_detectors = []
    
    for detector in detector_details:
        # Extract detector ID from the response
        detector_id = detector.get("DetectorId")
        if not detector_id:
            logger.warning(f"Detector missing DetectorId in region {region}")
            continue

        # Create ARN for the detector
        # GuardDuty detector ARN format: arn:aws:guardduty:region:account-id:detector/detector-id
        # We'll construct this in the load function since we have the account ID there
        
        transformed_detector = {
            "DetectorId": detector_id,
            "Status": detector.get("Status"),
            "ServiceRole": detector.get("ServiceRole"),
            "FindingPublishingFrequency": detector.get("FindingPublishingFrequency"),
            "CreatedAt": detector.get("CreatedAt"),
            "UpdatedAt": detector.get("UpdatedAt"),
            "Region": region,
        }
        
        transformed_detectors.append(transformed_detector)
    
    return transformed_detectors


@timeit
def load_guardduty_detectors(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    region: str,
    aws_account_id: str,
    update_tag: int,
) -> None:
    """
    Load GuardDuty detector information into the graph.
    """
    # Add ARN to each detector
    for detector in data:
        detector_id = detector.get("DetectorId")
        if detector_id:
            detector["Arn"] = f"arn:aws:guardduty:{region}:{aws_account_id}:detector/{detector_id}"

    load(
        neo4j_session,
        GuardDutyDetectorSchema(),
        data,
        lastupdated=update_tag,
        Region=region,
        AWS_ID=aws_account_id,
    )


@timeit
def cleanup_guardduty(
    neo4j_session: neo4j.Session, common_job_parameters: Dict
) -> None:
    """
    Run GuardDuty cleanup job.
    """
    logger.debug("Running GuardDuty cleanup job.")
    # Cleanup findings
    cleanup_job = GraphJob.from_node_schema(
        GuardDutyFindingSchema(), common_job_parameters
    )
    cleanup_job.run(neo4j_session)
    
    # Cleanup detectors
    detector_cleanup_job = GraphJob.from_node_schema(
        GuardDutyDetectorSchema(), common_job_parameters
    )
    detector_cleanup_job.run(neo4j_session)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: List[str],
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: Dict,
) -> None:
    """
    Sync GuardDuty detectors and findings for all regions.
    Severity threshold filter is obtained from common_job_parameters.
    """
    # Get severity threshold from common job parameters
    severity_threshold = common_job_parameters.get("aws_guardduty_severity_threshold")
    for region in regions:
        logger.info(
            f"Syncing GuardDuty detectors and findings for {region} in account {current_aws_account_id}"
        )

        # Get all detectors in the region
        detector_ids = get_detectors(boto3_session, region)

        if not detector_ids:
            logger.info(f"No GuardDuty detectors found in region {region}, skipping.")
            continue

        # Sync detectors first
        detector_details = get_detector_details(boto3_session, region, detector_ids)
        transformed_detectors = transform_detector_details(detector_details, region)
        load_guardduty_detectors(
            neo4j_session,
            transformed_detectors,
            region,
            current_aws_account_id,
            update_tag,
        )

        # Then sync findings
        all_findings = []

        # Get findings for each detector
        for detector_id in detector_ids:
            findings = get_findings(
                boto3_session, region, detector_id, severity_threshold
            )
            all_findings.extend(findings)

        transformed_findings = transform_findings(all_findings)

        load_guardduty_findings(
            neo4j_session,
            transformed_findings,
            region,
            current_aws_account_id,
            update_tag,
        )

    # Cleanup and metadata update (outside region loop)
    cleanup_guardduty(neo4j_session, common_job_parameters)

    # Update metadata for both detectors and findings
    merge_module_sync_metadata(
        neo4j_session,
        group_type="AWSAccount",
        group_id=current_aws_account_id,
        synced_type="GuardDutyDetector",
        update_tag=update_tag,
        stat_handler=stat_handler,
    )
    merge_module_sync_metadata(
        neo4j_session,
        group_type="AWSAccount",
        group_id=current_aws_account_id,
        synced_type="GuardDutyFinding",
        update_tag=update_tag,
        stat_handler=stat_handler,
    )
