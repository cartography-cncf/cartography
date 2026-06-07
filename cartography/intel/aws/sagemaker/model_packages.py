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
from cartography.models.aws.sagemaker.model_package import (
    AWSSageMakerModelPackageSchema,
)
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@sagemaker_handle_regions
def get_model_packages(
    boto3_session: boto3.session.Session,
    region: str,
) -> list[dict[str, Any]]:
    """
    Get all SageMaker Model Packages in the given region.
    """
    client = create_boto3_client(boto3_session, "sagemaker", region_name=region)
    paginator = client.get_paginator("list_model_packages")
    model_packages: list[dict[str, Any]] = []

    # Get all model package ARNs
    model_package_arns: list[str] = []
    for page in paginator.paginate():
        for package in page.get("ModelPackageSummaryList", []):
            model_package_arns.append(package["ModelPackageArn"])

    # Get detailed information for each model package
    for package_arn in model_package_arns:
        response = client.describe_model_package(ModelPackageName=package_arn)
        model_packages.append(response)

    return model_packages


def transform_model_packages(
    model_packages: list[dict[str, Any]],
    region: str,
) -> list[dict[str, Any]]:
    """
    Transform model package data for loading into Neo4j.
    """
    transformed_packages = []

    for package in model_packages:
        # Extract S3 bucket from model artifacts in inference specification
        model_artifacts_bucket_id = None
        inference_spec = package.get("InferenceSpecification", {})
        containers = inference_spec.get("Containers", [])
        if containers and len(containers) > 0:
            model_data_url = containers[0].get("ModelDataUrl")
            if model_data_url:
                model_artifacts_bucket_id = extract_bucket_name_from_s3_uri(
                    model_data_url
                )

        transformed_package = {
            "ModelPackageArn": package.get("ModelPackageArn"),
            "ModelPackageName": package.get("ModelPackageName"),
            "ModelPackageGroupName": package.get("ModelPackageGroupName"),
            "ModelPackageVersion": package.get("ModelPackageVersion"),
            "ModelPackageDescription": package.get("ModelPackageDescription"),
            "ModelPackageStatus": package.get("ModelPackageStatus"),
            "CreationTime": package.get("CreationTime"),
            "LastModifiedTime": package.get("LastModifiedTime"),
            "ModelApprovalStatus": package.get("ModelApprovalStatus"),
            "ModelArtifactsS3BucketId": model_artifacts_bucket_id,
            "Region": region,
        }
        transformed_packages.append(transformed_package)

    return transformed_packages


@timeit
def load_model_packages(
    neo4j_session: neo4j.Session,
    model_packages: list[dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    """
    Load model packages into Neo4j.
    """
    load(
        neo4j_session,
        AWSSageMakerModelPackageSchema(),
        model_packages,
        Region=region,
        AWS_ID=current_aws_account_id,
        lastupdated=aws_update_tag,
    )


@timeit
def cleanup_model_packages(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Remove model packages that no longer exist in AWS.
    """
    GraphJob.from_node_schema(
        AWSSageMakerModelPackageSchema(),
        common_job_parameters,
    ).run(neo4j_session)


@timeit
def sync_model_packages(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: list[str],
    current_aws_account_id: str,
    aws_update_tag: int,
    common_job_parameters: dict[str, Any],
    skip_regions: set[str],
) -> set[str]:
    """
    Sync SageMaker Model Packages for all specified regions.
    """
    return sync_sagemaker_resource(
        neo4j_session=neo4j_session,
        boto3_session=boto3_session,
        regions=regions,
        current_aws_account_id=current_aws_account_id,
        aws_update_tag=aws_update_tag,
        common_job_parameters=common_job_parameters,
        skip_regions=skip_regions,
        submodule_name="model_packages",
        get_resources=get_model_packages,
        transform_resources=transform_model_packages,
        load_resources=load_model_packages,
        cleanup_resources=cleanup_model_packages,
    )
