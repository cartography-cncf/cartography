import logging
from typing import Any
from typing import Dict
from typing import List

import boto3
import neo4j
from botocore.exceptions import ClientError
from botocore.exceptions import ConnectionClosedError
from botocore.exceptions import ConnectTimeoutError
from botocore.exceptions import ReadTimeoutError
from botocore.parsers import ResponseParserError

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.aws.util.botocore_config import create_boto3_client
from cartography.intel.aws.util.botocore_config import get_botocore_config
from cartography.models.aws.glue.connection import GlueConnectionSchema
from cartography.models.aws.glue.job import GlueJobSchema
from cartography.util import aws_handle_regions
from cartography.util import timeit

logger = logging.getLogger(__name__)

_RETRYABLE_HTTP_STATUS_CODES = {429, 500, 502, 503, 504}


class GlueTransientRegionFailure(Exception):
    pass


def _is_retryable_glue_error(error: ClientError) -> bool:
    error_code = error.response.get("Error", {}).get("Code", "")
    status_code = error.response.get("ResponseMetadata", {}).get("HTTPStatusCode")
    return (
        error_code
        in {
            "InternalFailure",
            "InternalServerException",
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


def _paginate_glue(
    paginator: Any, result_key: str, operation: str
) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    try:
        for page in paginator.paginate():
            items.extend(page.get(result_key, []))
    except ClientError as error:
        if _is_retryable_glue_error(error):
            raise GlueTransientRegionFailure(
                f"AWS SDK retries were exhausted for transient {operation} failure"
            ) from error
        raise
    except (
        ConnectionClosedError,
        ConnectTimeoutError,
        ReadTimeoutError,
        ResponseParserError,
    ) as error:
        raise GlueTransientRegionFailure(
            f"Encountered a transient regional Glue endpoint failure while calling {operation}"
        ) from error
    return items


@timeit
@aws_handle_regions
def get_glue_connections(
    boto3_session: boto3.Session, region: str
) -> List[Dict[str, Any]]:
    client = create_boto3_client(
        boto3_session, "glue", region_name=region, config=get_botocore_config()
    )
    paginator = client.get_paginator("get_connections")
    return _paginate_glue(paginator, "ConnectionList", "GetConnections")


@timeit
@aws_handle_regions
def get_glue_jobs(boto3_session: boto3.Session, region: str) -> List[Dict[str, Any]]:
    client = create_boto3_client(
        boto3_session, "glue", region_name=region, config=get_botocore_config()
    )
    paginator = client.get_paginator("get_jobs")
    return _paginate_glue(paginator, "Jobs", "GetJobs")


def transform_glue_job(jobs: List[Dict[str, Any]], region: str) -> List[Dict[str, Any]]:
    """
    Transform Glue job data for ingestion
    """
    transformed_jobs = []
    for job in jobs:
        transformed_job = {
            "Name": job["Name"],
            "ProfileName": job.get("ProfileName"),
            "JobMode": job.get("JobMode"),
            "Connections": job.get("Connections", {}).get("Connections"),
            "Region": region,
            "Description": job.get("Description"),
        }
        transformed_jobs.append(transformed_job)
    return transformed_jobs


def transform_glue_connections(
    connections: List[Dict[str, Any]], region: str
) -> List[Dict[str, Any]]:
    """
    Transform Glue connection data for ingestion
    """
    transformed_connections = []
    for connection in connections:
        transformed_connection = {
            "Name": connection["Name"],
            "Description": connection.get("Description"),
            "ConnectionType": connection.get("ConnectionType"),
            "Status": connection.get("Status"),
            "StatusReason": connection.get("StatusReason"),
            "AuthenticationType": connection.get("AuthenticationConfiguration", {}).get(
                "AuthenticationType"
            ),
            "SecretArn": connection.get("AuthenticationConfiguration", {}).get(
                "SecretArn"
            ),
            "Region": region,
        }
        transformed_connections.append(transformed_connection)
    return transformed_connections


@timeit
def load_glue_connections(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    logger.info(
        f"Loading Glue {len(data)} connections for region '{region}' into graph.",
    )
    load(
        neo4j_session,
        GlueConnectionSchema(),
        data,
        lastupdated=aws_update_tag,
        Region=region,
        AWS_ID=current_aws_account_id,
    )


@timeit
def load_glue_jobs(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    logger.info(
        f"Loading Glue {len(data)} jobs for region '{region}' into graph.",
    )
    load(
        neo4j_session,
        GlueJobSchema(),
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
    logger.debug("Running Glue cleanup job.")
    GraphJob.from_node_schema(GlueConnectionSchema(), common_job_parameters).run(
        neo4j_session
    )
    GraphJob.from_node_schema(GlueJobSchema(), common_job_parameters).run(neo4j_session)


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
            f"Syncing Glue for region '{region}' in account '{current_aws_account_id}'.",
        )
        try:
            connections = get_glue_connections(boto3_session, region)
            jobs = get_glue_jobs(boto3_session, region)
        except GlueTransientRegionFailure as error:
            cleanup_safe = False
            logger.warning(
                "Skipping Glue sync for account %s in region %s after transient Glue failure: %s",
                current_aws_account_id,
                region,
                error,
            )
            continue

        load_glue_connections(
            neo4j_session,
            transform_glue_connections(connections, region),
            region,
            current_aws_account_id,
            update_tag,
        )
        load_glue_jobs(
            neo4j_session,
            transform_glue_job(jobs, region),
            region,
            current_aws_account_id,
            update_tag,
        )

    if cleanup_safe:
        cleanup(neo4j_session, common_job_parameters)
    else:
        logger.warning(
            "Skipping Glue cleanup for account %s because one or more regions had transient Glue failures. Preserving last-known-good Glue state.",
            current_aws_account_id,
        )
