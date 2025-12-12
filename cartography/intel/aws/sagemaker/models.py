import logging
from typing import Any

import boto3
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.aws.sagemaker.util import extract_bucket_name_from_s3_uri
from cartography.models.aws.sagemaker.model import AWSSageMakerModelSchema
from cartography.util import aws_handle_regions
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_models(
    boto3_session: boto3.session.Session,
    region: str,
) -> list[dict[str, Any]]:
    """
    Get all SageMaker Models in the given region.
    """
    client = boto3_session.client("sagemaker", region_name=region)
    paginator = client.get_paginator("list_models")
    models: list[dict[str, Any]] = []

    # Get all model names
    model_names: list[str] = []
    for page in paginator.paginate():
        for model in page.get("Models", []):
            model_names.append(model["ModelName"])

    # Get detailed information for each model
    for model_name in model_names:
        response = client.describe_model(ModelName=model_name)
        models.append(response)

    return models


def transform_models(
    models: list[dict[str, Any]],
    region: str,
) -> list[dict[str, Any]]:
    """
    Transform model data for loading into Neo4j.
    """
    transformed_models = []

    for model in models:
        # Extract S3 bucket from model artifacts
        # Models can have Containers (array) or PrimaryContainer (single object)
        model_artifacts_bucket_id = None
        model_package_name = None

        # Try Containers first (newer API)
        containers = model.get("Containers", [])
        if containers and len(containers) > 0:
            first_container = containers[0]
            model_data_url = first_container.get("ModelDataUrl")
            model_package_name = first_container.get("ModelPackageName")
        else:
            # Fall back to PrimaryContainer (older API)
            primary_container = model.get("PrimaryContainer", {})
            model_data_url = primary_container.get("ModelDataUrl")
            model_package_name = primary_container.get("ModelPackageName")

        if model_data_url:
            model_artifacts_bucket_id = extract_bucket_name_from_s3_uri(model_data_url)

        # Extract container image
        container_image = None
        if containers and len(containers) > 0:
            container_image = containers[0].get("Image")
        else:
            primary_container = model.get("PrimaryContainer", {})
            container_image = primary_container.get("Image")

        transformed_model = {
            "ModelArn": model.get("ModelArn"),
            "ModelName": model.get("ModelName"),
            "CreationTime": model.get("CreationTime"),
            "ExecutionRoleArn": model.get("ExecutionRoleArn"),
            "PrimaryContainerImage": container_image,
            "ModelPackageName": model_package_name,
            "ModelPackageArn": model_package_name,  # ModelPackageName can be an ARN
            "ModelArtifactsS3BucketId": model_artifacts_bucket_id,
            "Region": region,
        }
        transformed_models.append(transformed_model)

    return transformed_models


@timeit
def load_models(
    neo4j_session: neo4j.Session,
    models: list[dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    """
    Load models into Neo4j.
    """
    load(
        neo4j_session,
        AWSSageMakerModelSchema(),
        models,
        Region=region,
        AWS_ID=current_aws_account_id,
        lastupdated=aws_update_tag,
    )


@timeit
def cleanup_models(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Remove models that no longer exist in AWS.
    """
    GraphJob.from_node_schema(
        AWSSageMakerModelSchema(),
        common_job_parameters,
    ).run(neo4j_session)


@timeit
def sync_models(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: list[str],
    current_aws_account_id: str,
    aws_update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Sync SageMaker Models for all specified regions.
    """
    for region in regions:
        logger.info(
            "Syncing SageMaker Models for region '%s' in account '%s'.",
            region,
            current_aws_account_id,
        )
        # Get models from AWS
        models = get_models(boto3_session, region)

        # Transform the data
        transformed_models = transform_models(models, region)

        # Load into Neo4j
        load_models(
            neo4j_session,
            transformed_models,
            region,
            current_aws_account_id,
            aws_update_tag,
        )

    # Cleanup old models
    cleanup_models(neo4j_session, common_job_parameters)
