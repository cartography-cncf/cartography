import json
import logging
from typing import Any
from typing import Dict
from typing import List

import boto3
import neo4j
from botocore.exceptions import ClientError
from botocore.exceptions import ConnectionClosedError
from botocore.exceptions import ConnectTimeoutError
from botocore.exceptions import EndpointConnectionError
from botocore.exceptions import ReadTimeoutError
from botocore.parsers import ResponseParserError

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.aws.util.botocore_config import create_boto3_client
from cartography.models.aws.cloudtrail.trail import CloudTrailTrailSchema
from cartography.util import aws_handle_regions
from cartography.util import timeit

logger = logging.getLogger(__name__)

_RETRYABLE_HTTP_STATUS_CODES = {429, 500, 502, 503, 504}


class CloudTrailTransientRegionFailure(Exception):
    pass


def _is_retryable_cloudtrail_error(error: ClientError) -> bool:
    error_code = error.response.get("Error", {}).get("Code", "")
    status_code = error.response.get("ResponseMetadata", {}).get("HTTPStatusCode")
    return (
        error_code
        in {
            "RequestLimitExceeded",
            "RequestThrottled",
            "RequestTimeout",
            "RequestTimeoutException",
            "ServiceUnavailable",
            "ServiceUnavailableException",
            "Throttling",
            "ThrottlingException",
            "TooManyRequestsException",
        }
        or status_code in _RETRYABLE_HTTP_STATUS_CODES
    )


@timeit
@aws_handle_regions
def get_cloudtrail_trails(
    boto3_session: boto3.Session, region: str, current_aws_account_id: str
) -> List[Dict[str, Any]]:
    client = create_boto3_client(boto3_session, "cloudtrail", region_name=region)

    try:
        trails = client.describe_trails()["trailList"]
    except ClientError as error:
        if _is_retryable_cloudtrail_error(error):
            raise CloudTrailTransientRegionFailure(
                "AWS SDK retries were exhausted for transient DescribeTrails failure"
            ) from error
        raise
    except (
        ConnectionClosedError,
        ConnectTimeoutError,
        EndpointConnectionError,
        ReadTimeoutError,
        ResponseParserError,
    ) as error:
        raise CloudTrailTransientRegionFailure(
            "Encountered a transient regional CloudTrail endpoint failure while calling DescribeTrails"
        ) from error

    trails_filtered = []
    for trail in trails:
        # Filter by home region to avoid duplicates across regions
        if trail.get("HomeRegion") != region:
            continue

        # Filter to only trails owned by this account.
        # Organization trails from other accounts are visible via describe_trails()
        # but should not be linked as RESOURCE of this account.
        # ARN format: arn:aws:cloudtrail:{region}:{account_id}:trail/{name}
        trail_arn = trail.get("TrailARN", "")
        arn_parts = trail_arn.split(":")
        if len(arn_parts) >= 5:
            trail_account_id = arn_parts[4]
            if trail_account_id != current_aws_account_id:
                logger.debug(
                    f"Skipping trail {trail_arn} - owned by account {trail_account_id}, "
                    f"not current account {current_aws_account_id}",
                )
                continue

        try:
            selectors = client.get_event_selectors(TrailName=trail["TrailARN"])
            trail["EventSelectors"] = selectors.get("EventSelectors", [])
            trail["AdvancedEventSelectors"] = selectors.get(
                "AdvancedEventSelectors",
                [],
            )
        except ClientError as error:
            if _is_retryable_cloudtrail_error(error):
                raise CloudTrailTransientRegionFailure(
                    f"AWS SDK retries were exhausted for transient GetEventSelectors failure on trail {trail['TrailARN']}"
                ) from error
            raise
        except (
            ConnectionClosedError,
            ConnectTimeoutError,
            EndpointConnectionError,
            ReadTimeoutError,
            ResponseParserError,
        ) as error:
            raise CloudTrailTransientRegionFailure(
                f"Encountered a transient regional CloudTrail endpoint failure while calling GetEventSelectors on trail {trail['TrailARN']}"
            ) from error
        trails_filtered.append(trail)

    return trails_filtered


def transform_cloudtrail_trails(
    trails: List[Dict[str, Any]], region: str
) -> List[Dict[str, Any]]:
    """
    Transform CloudTrail trail data for ingestion
    """
    for trail in trails:
        arn = trail.get("CloudWatchLogsLogGroupArn")
        if arn:
            trail["CloudWatchLogsLogGroupArn"] = arn.split(":*")[0]
        trail["EventSelectors"] = json.dumps(trail.get("EventSelectors", []))
        trail["AdvancedEventSelectors"] = json.dumps(
            trail.get("AdvancedEventSelectors", []),
        )

    return trails


@timeit
def load_cloudtrail_trails(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    logger.info(
        f"Loading CloudTrail {len(data)} trails for region '{region}' into graph.",
    )
    load(
        neo4j_session,
        CloudTrailTrailSchema(),
        data,
        lastupdated=aws_update_tag,
        Region=region,
        AWS_ID=current_aws_account_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict[str, Any],
) -> None:
    logger.debug("Running CloudTrail cleanup job.")
    cleanup_job = GraphJob.from_node_schema(
        CloudTrailTrailSchema(), common_job_parameters
    )
    cleanup_job.run(neo4j_session)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: List[str],
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:
    cleanup_safe = True
    for region in regions:
        logger.info(
            f"Syncing CloudTrail for region '{region}' in account '{current_aws_account_id}'.",
        )
        try:
            trails_filtered = get_cloudtrail_trails(
                boto3_session, region, current_aws_account_id
            )
        except CloudTrailTransientRegionFailure as error:
            cleanup_safe = False
            logger.warning(
                "Skipping CloudTrail sync for account %s in region %s after transient CloudTrail failure: %s",
                current_aws_account_id,
                region,
                error,
            )
            continue
        trails = transform_cloudtrail_trails(trails_filtered, region)

        load_cloudtrail_trails(
            neo4j_session,
            trails,
            region,
            current_aws_account_id,
            update_tag,
        )

    if cleanup_safe:
        cleanup(neo4j_session, common_job_parameters)
    else:
        logger.warning(
            "Skipping CloudTrail cleanup for account %s because one or more regions had transient CloudTrail failures. Preserving last-known-good CloudTrail state.",
            current_aws_account_id,
        )
