import logging
from typing import Any

import boto3
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.aws.sagemaker.util import sagemaker_handle_regions
from cartography.intel.aws.sagemaker.util import sync_sagemaker_resource
from cartography.intel.aws.util.botocore_config import create_boto3_client
from cartography.models.aws.sagemaker.model_package_group import (
    AWSSageMakerModelPackageGroupSchema,
)
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@sagemaker_handle_regions
def get_model_package_groups(
    boto3_session: boto3.session.Session,
    region: str,
) -> list[dict[str, Any]]:
    """
    Get all SageMaker Model Package Groups in the given region.
    """
    client = create_boto3_client(boto3_session, "sagemaker", region_name=region)
    paginator = client.get_paginator("list_model_package_groups")
    model_package_groups: list[dict[str, Any]] = []

    # Get all model package group names
    model_package_group_names: list[str] = []
    for page in paginator.paginate():
        for group in page.get("ModelPackageGroupSummaryList", []):
            model_package_group_names.append(group["ModelPackageGroupName"])

    # Get detailed information for each model package group
    for group_name in model_package_group_names:
        response = client.describe_model_package_group(ModelPackageGroupName=group_name)
        model_package_groups.append(response)

    return model_package_groups


def transform_model_package_groups(
    model_package_groups: list[dict[str, Any]],
    region: str,
) -> list[dict[str, Any]]:
    """
    Transform model package group data for loading into Neo4j.
    """
    transformed_groups = []

    for group in model_package_groups:
        transformed_group = {
            "ModelPackageGroupArn": group.get("ModelPackageGroupArn"),
            "ModelPackageGroupName": group.get("ModelPackageGroupName"),
            "ModelPackageGroupDescription": group.get("ModelPackageGroupDescription"),
            "CreationTime": group.get("CreationTime"),
            "ModelPackageGroupStatus": group.get("ModelPackageGroupStatus"),
            "Region": region,
        }
        transformed_groups.append(transformed_group)

    return transformed_groups


@timeit
def load_model_package_groups(
    neo4j_session: neo4j.Session,
    model_package_groups: list[dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    """
    Load model package groups into Neo4j.
    """
    load(
        neo4j_session,
        AWSSageMakerModelPackageGroupSchema(),
        model_package_groups,
        Region=region,
        AWS_ID=current_aws_account_id,
        lastupdated=aws_update_tag,
    )


@timeit
def cleanup_model_package_groups(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Remove model package groups that no longer exist in AWS.
    """
    GraphJob.from_node_schema(
        AWSSageMakerModelPackageGroupSchema(),
        common_job_parameters,
    ).run(neo4j_session)


@timeit
def sync_model_package_groups(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: list[str],
    current_aws_account_id: str,
    aws_update_tag: int,
    common_job_parameters: dict[str, Any],
    skip_regions: set[str],
) -> set[str]:
    """
    Sync SageMaker Model Package Groups for all specified regions.
    """
    return sync_sagemaker_resource(
        neo4j_session=neo4j_session,
        boto3_session=boto3_session,
        regions=regions,
        current_aws_account_id=current_aws_account_id,
        aws_update_tag=aws_update_tag,
        common_job_parameters=common_job_parameters,
        skip_regions=skip_regions,
        submodule_name="model_package_groups",
        get_resources=get_model_package_groups,
        transform_resources=transform_model_package_groups,
        load_resources=load_model_package_groups,
        cleanup_resources=cleanup_model_package_groups,
    )
