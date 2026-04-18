import logging
from typing import Any

import boto3
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.aws.sagemaker.util import extract_bucket_name_from_s3_uri
from cartography.intel.aws.sagemaker.util import sagemaker_handle_regions
from cartography.intel.aws.sagemaker.util import sync_sagemaker_resource
from cartography.intel.aws.util.botocore_config import create_boto3_client
from cartography.models.aws.sagemaker.transform_job import (
    AWSSageMakerTransformJobSchema,
)
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@sagemaker_handle_regions
def get_transform_jobs(
    boto3_session: boto3.session.Session,
    region: str,
) -> list[dict[str, Any]]:
    """
    Get all SageMaker Transform Jobs in the given region.
    """
    client = create_boto3_client(boto3_session, "sagemaker", region_name=region)
    paginator = client.get_paginator("list_transform_jobs")
    transform_jobs: list[dict[str, Any]] = []

    # Get all transform job names
    transform_job_names: list[str] = []
    for page in paginator.paginate():
        for job in page.get("TransformJobSummaries", []):
            transform_job_names.append(job["TransformJobName"])

    # Get detailed information for each transform job
    for job_name in transform_job_names:
        response = client.describe_transform_job(TransformJobName=job_name)
        transform_jobs.append(response)

    return transform_jobs


def transform_transform_jobs(
    transform_jobs: list[dict[str, Any]],
    region: str,
) -> list[dict[str, Any]]:
    """
    Transform transform job data for loading into Neo4j.
    """
    transformed_jobs = []

    for job in transform_jobs:
        # Extract output S3 bucket
        output_bucket_id = None
        transform_output = job.get("TransformOutput", {})
        s3_output_path = transform_output.get("S3OutputPath")
        if s3_output_path:
            output_bucket_id = extract_bucket_name_from_s3_uri(s3_output_path)

        transformed_job = {
            "TransformJobArn": job.get("TransformJobArn"),
            "TransformJobName": job.get("TransformJobName"),
            "TransformJobStatus": job.get("TransformJobStatus"),
            "ModelName": job.get("ModelName"),
            "MaxConcurrentTransforms": job.get("MaxConcurrentTransforms"),
            "MaxPayloadInMB": job.get("MaxPayloadInMB"),
            "BatchStrategy": job.get("BatchStrategy"),
            "CreationTime": job.get("CreationTime"),
            "TransformStartTime": job.get("TransformStartTime"),
            "TransformEndTime": job.get("TransformEndTime"),
            "OutputDataS3BucketId": output_bucket_id,
            "Region": region,
        }
        transformed_jobs.append(transformed_job)

    return transformed_jobs


@timeit
def load_transform_jobs(
    neo4j_session: neo4j.Session,
    transform_jobs: list[dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    """
    Load transform jobs into Neo4j.
    """
    load(
        neo4j_session,
        AWSSageMakerTransformJobSchema(),
        transform_jobs,
        Region=region,
        AWS_ID=current_aws_account_id,
        lastupdated=aws_update_tag,
    )


@timeit
def cleanup_transform_jobs(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Remove transform jobs that no longer exist in AWS.
    """
    GraphJob.from_node_schema(
        AWSSageMakerTransformJobSchema(),
        common_job_parameters,
    ).run(neo4j_session)


@timeit
def sync_transform_jobs(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: list[str],
    current_aws_account_id: str,
    aws_update_tag: int,
    common_job_parameters: dict[str, Any],
    skip_regions: set[str],
) -> set[str]:
    """
    Sync SageMaker Transform Jobs for all specified regions.
    """
    return sync_sagemaker_resource(
        neo4j_session=neo4j_session,
        boto3_session=boto3_session,
        regions=regions,
        current_aws_account_id=current_aws_account_id,
        aws_update_tag=aws_update_tag,
        common_job_parameters=common_job_parameters,
        skip_regions=skip_regions,
        submodule_name="transform_jobs",
        get_resources=get_transform_jobs,
        transform_resources=transform_transform_jobs,
        load_resources=load_transform_jobs,
        cleanup_resources=cleanup_transform_jobs,
    )
