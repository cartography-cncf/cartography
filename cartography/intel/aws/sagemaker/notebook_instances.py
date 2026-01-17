import logging
from typing import Any

import boto3
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.aws.sagemaker.notebook_instance import (
    AWSSageMakerNotebookInstanceSchema,
)
from cartography.util import aws_handle_regions
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_notebook_instances(
    boto3_session: boto3.session.Session,
    region: str,
) -> list[dict[str, Any]]:
    """
    Get all SageMaker Notebook Instances in the given region.
    """
    client = boto3_session.client("sagemaker", region_name=region)
    paginator = client.get_paginator("list_notebook_instances")
    notebook_instances: list[dict[str, Any]] = []

    # Get all notebook instance names
    notebook_instance_names: list[str] = []
    for page in paginator.paginate():
        for instance in page.get("NotebookInstances", []):
            notebook_instance_names.append(instance["NotebookInstanceName"])

    # Get detailed information for each notebook instance
    for notebook_instance_name in notebook_instance_names:
        response = client.describe_notebook_instance(
            NotebookInstanceName=notebook_instance_name
        )
        notebook_instances.append(response)

    return notebook_instances


def transform_notebook_instances(
    notebook_instances: list[dict[str, Any]],
    region: str,
) -> list[dict[str, Any]]:
    """
    Transform notebook instance data for loading into Neo4j.
    """
    transformed_instances = []

    for instance in notebook_instances:
        transformed_instance = {
            "NotebookInstanceArn": instance.get("NotebookInstanceArn"),
            "NotebookInstanceName": instance.get("NotebookInstanceName"),
            "NotebookInstanceStatus": instance.get("NotebookInstanceStatus"),
            "InstanceType": instance.get("InstanceType"),
            "Url": instance.get("Url"),
            "CreationTime": instance.get("CreationTime"),
            "LastModifiedTime": instance.get("LastModifiedTime"),
            "SubnetId": instance.get("SubnetId"),
            "SecurityGroups": instance.get("SecurityGroups"),
            "RoleArn": instance.get("RoleArn"),
            "KmsKeyId": instance.get("KmsKeyId"),
            "NetworkInterfaceId": instance.get("NetworkInterfaceId"),
            "DirectInternetAccess": instance.get("DirectInternetAccess"),
            "VolumeSizeInGB": instance.get("VolumeSizeInGB"),
            "RootAccess": instance.get("RootAccess"),
            "PlatformIdentifier": instance.get("PlatformIdentifier"),
            "Region": region,
        }
        transformed_instances.append(transformed_instance)

    return transformed_instances


@timeit
def load_notebook_instances(
    neo4j_session: neo4j.Session,
    notebook_instances: list[dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    """
    Load notebook instances into Neo4j.
    """
    load(
        neo4j_session,
        AWSSageMakerNotebookInstanceSchema(),
        notebook_instances,
        Region=region,
        AWS_ID=current_aws_account_id,
        lastupdated=aws_update_tag,
    )


@timeit
def cleanup_notebook_instances(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Remove notebook instances that no longer exist in AWS.
    """
    GraphJob.from_node_schema(
        AWSSageMakerNotebookInstanceSchema(),
        common_job_parameters,
    ).run(neo4j_session)


@timeit
def sync_notebook_instances(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: list[str],
    current_aws_account_id: str,
    aws_update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Sync SageMaker Notebook Instances for all specified regions.
    """
    for region in regions:
        logger.info(
            "Syncing SageMaker Notebook Instances for region '%s' in account '%s'.",
            region,
            current_aws_account_id,
        )
        # Get notebook instances from AWS
        notebook_instances = get_notebook_instances(boto3_session, region)

        # Transform the data
        transformed_instances = transform_notebook_instances(
            notebook_instances,
            region,
        )

        # Load into Neo4j
        load_notebook_instances(
            neo4j_session,
            transformed_instances,
            region,
            current_aws_account_id,
            aws_update_tag,
        )

    # Cleanup old notebook instances
    cleanup_notebook_instances(neo4j_session, common_job_parameters)
