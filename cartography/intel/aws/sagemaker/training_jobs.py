import logging
from typing import Any

import boto3
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.aws.sagemaker.util import extract_bucket_name_from_s3_uri
from cartography.models.aws.sagemaker.training_job import AWSSageMakerTrainingJobSchema
from cartography.util import aws_handle_regions
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_training_jobs(
    boto3_session: boto3.session.Session,
    region: str,
) -> list[dict[str, Any]]:
    """
    Get all SageMaker Training Jobs in the given region.
    """
    client = boto3_session.client("sagemaker", region_name=region)
    paginator = client.get_paginator("list_training_jobs")
    training_jobs: list[dict[str, Any]] = []

    # Get all training job names
    training_job_names: list[str] = []
    for page in paginator.paginate():
        for job in page.get("TrainingJobSummaries", []):
            training_job_names.append(job["TrainingJobName"])

    # Get detailed information for each training job
    for job_name in training_job_names:
        response = client.describe_training_job(TrainingJobName=job_name)
        training_jobs.append(response)

    return training_jobs


def transform_training_jobs(
    training_jobs: list[dict[str, Any]],
    region: str,
) -> list[dict[str, Any]]:
    """
    Transform training job data for loading into Neo4j.
    """
    transformed_jobs = []

    for job in training_jobs:
        # Extract input S3 bucket from the first channel. Training jobs can have multiple
        # channels (e.g., train, validation), but typically use the same bucket for all.
        input_bucket_id = None
        input_data_config = job.get("InputDataConfig", [])
        if input_data_config and len(input_data_config) > 0:
            s3_uri = (
                input_data_config[0]
                .get("DataSource", {})
                .get("S3DataSource", {})
                .get("S3Uri")
            )
            if s3_uri:
                input_bucket_id = extract_bucket_name_from_s3_uri(s3_uri)

        # Extract output S3 bucket
        output_bucket_id = None
        output_s3_path = job.get("OutputDataConfig", {}).get("S3OutputPath")
        if output_s3_path:
            output_bucket_id = extract_bucket_name_from_s3_uri(output_s3_path)

        # Extract AlgorithmSpecification fields
        algo_spec = job.get("AlgorithmSpecification", {})

        transformed_job = {
            "TrainingJobArn": job.get("TrainingJobArn"),
            "TrainingJobName": job.get("TrainingJobName"),
            "TrainingJobStatus": job.get("TrainingJobStatus"),
            "CreationTime": job.get("CreationTime"),
            "TrainingStartTime": job.get("TrainingStartTime"),
            "TrainingEndTime": job.get("TrainingEndTime"),
            "LastModifiedTime": job.get("LastModifiedTime"),
            "SecondaryStatus": job.get("SecondaryStatus"),
            "AlgorithmSpecification": {
                "TrainingImage": algo_spec.get("TrainingImage"),
                "TrainingInputMode": algo_spec.get("TrainingInputMode"),
            },
            "RoleArn": job.get("RoleArn"),
            "BillableTimeInSeconds": job.get("BillableTimeInSeconds"),
            "TrainingTimeInSeconds": job.get("TrainingTimeInSeconds"),
            "EnableNetworkIsolation": job.get("EnableNetworkIsolation"),
            "EnableInterContainerTrafficEncryption": job.get(
                "EnableInterContainerTrafficEncryption"
            ),
            "EnableManagedSpotTraining": job.get("EnableManagedSpotTraining"),
            "InputDataS3BucketId": input_bucket_id,
            "OutputDataS3BucketId": output_bucket_id,
            "Region": region,
        }
        transformed_jobs.append(transformed_job)

    return transformed_jobs


@timeit
def load_training_jobs(
    neo4j_session: neo4j.Session,
    training_jobs: list[dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    """
    Load training jobs into Neo4j.
    """
    load(
        neo4j_session,
        AWSSageMakerTrainingJobSchema(),
        training_jobs,
        Region=region,
        AWS_ID=current_aws_account_id,
        lastupdated=aws_update_tag,
    )


@timeit
def cleanup_training_jobs(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Remove training jobs that no longer exist in AWS.
    """
    GraphJob.from_node_schema(
        AWSSageMakerTrainingJobSchema(),
        common_job_parameters,
    ).run(neo4j_session)


@timeit
def sync_training_jobs(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: list[str],
    current_aws_account_id: str,
    aws_update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Sync SageMaker Training Jobs for all specified regions.
    """
    for region in regions:
        logger.info(
            "Syncing SageMaker Training Jobs for region '%s' in account '%s'.",
            region,
            current_aws_account_id,
        )
        # Get training jobs from AWS
        training_jobs = get_training_jobs(boto3_session, region)

        # Transform the data
        transformed_jobs = transform_training_jobs(training_jobs, region)

        # Load into Neo4j
        load_training_jobs(
            neo4j_session,
            transformed_jobs,
            region,
            current_aws_account_id,
            aws_update_tag,
        )

    # Cleanup old training jobs
    cleanup_training_jobs(neo4j_session, common_job_parameters)
