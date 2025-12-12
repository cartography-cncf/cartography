import logging
from typing import Any
from typing import Dict
from typing import List

import boto3
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.aws.sagemaker.model_package_group import (
    AWSSageMakerModelPackageGroupSchema,
)
from cartography.util import aws_handle_regions
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_model_package_groups(
    boto3_session: boto3.session.Session,
    region: str,
) -> List[Dict[str, Any]]:
    """
    Get all SageMaker Model Package Groups in the given region.
    """
    client = boto3_session.client("sagemaker", region_name=region)
    paginator = client.get_paginator("list_model_package_groups")
    model_package_groups: List[Dict[str, Any]] = []

    # Get all model package group names
    model_package_group_names: List[str] = []
    for page in paginator.paginate():
        for group in page.get("ModelPackageGroupSummaryList", []):
            model_package_group_names.append(group["ModelPackageGroupName"])

    # Get detailed information for each model package group
    for group_name in model_package_group_names:
        try:
            response = client.describe_model_package_group(
                ModelPackageGroupName=group_name
            )
            model_package_groups.append(response)
        except client.exceptions.ClientError as e:
            logger.warning(
                f"Failed to describe model package group {group_name} in {region}: {e}",
                exc_info=True,
            )
            continue

    return model_package_groups


def transform_model_package_groups(
    model_package_groups: List[Dict[str, Any]],
    region: str,
) -> List[Dict[str, Any]]:
    """
    Transform model package group data for loading into Neo4j.
    """
    transformed_groups = []

    for group in model_package_groups:
        transformed_group = {
            "ModelPackageGroupArn": group.get("ModelPackageGroupArn"),
            "ModelPackageGroupName": group.get("ModelPackageGroupName"),
            "CreationTime": group.get("CreationTime"),
            "ModelPackageGroupStatus": group.get("ModelPackageGroupStatus"),
            "Region": region,
        }
        transformed_groups.append(transformed_group)

    return transformed_groups


@timeit
def load_model_package_groups(
    neo4j_session: neo4j.Session,
    model_package_groups: List[Dict[str, Any]],
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
    common_job_parameters: Dict[str, Any],
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
    regions: List[str],
    current_aws_account_id: str,
    aws_update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:
    """
    Sync SageMaker Model Package Groups for all specified regions.
    """
    for region in regions:
        logger.info(
            "Syncing SageMaker Model Package Groups for region '%s' in account '%s'.",
            region,
            current_aws_account_id,
        )
        # Get model package groups from AWS
        model_package_groups = get_model_package_groups(boto3_session, region)

        # Transform the data
        transformed_groups = transform_model_package_groups(
            model_package_groups, region
        )

        # Load into Neo4j
        load_model_package_groups(
            neo4j_session,
            transformed_groups,
            region,
            current_aws_account_id,
            aws_update_tag,
        )

    # Cleanup old model package groups
    cleanup_model_package_groups(neo4j_session, common_job_parameters)
