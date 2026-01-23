import json
import logging
from typing import Any
from typing import Dict
from typing import List

import boto3
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.aws.ec2.util import get_botocore_config
from cartography.models.aws.cloudformation.stack import CloudFormationStackSchema
from cartography.util import aws_handle_regions
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_cloudformation_stacks(
    boto3_session: boto3.Session, region: str
) -> List[Dict[str, Any]]:
    client = boto3_session.client(
        "cloudformation", region_name=region, config=get_botocore_config()
    )
    paginator = client.get_paginator("describe_stacks")
    stacks: List[Dict[str, Any]] = []
    for page in paginator.paginate():
        stacks.extend(page["Stacks"])
    return stacks


def transform_cloudformation_stacks(
    stacks: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Transform CloudFormation stack data for ingestion.
    Ensures all properties are Neo4j-serializable.
    """
    for stack in stacks:
        if stack.get("Tags"):
            stack["Tags"] = json.dumps(stack["Tags"])

        if stack.get("RollbackConfiguration"):
            stack["RollbackConfiguration"] = json.dumps(
                stack["RollbackConfiguration"],
            )

        if stack.get("DriftInformation"):
            stack["DriftInformation"] = json.dumps(stack["DriftInformation"])

    return stacks


@timeit
def load_cloudformation_stacks(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    logger.info(
        "Loading %d CloudFormation stacks for region '%s' into graph.",
        len(data),
        region,
    )
    load(
        neo4j_session,
        CloudFormationStackSchema(),
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
    logger.debug("Running CloudFormation cleanup job.")
    GraphJob.from_node_schema(CloudFormationStackSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: List[str],
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:
    for region in regions:
        logger.info(
            "Syncing CloudFormation stacks for region '%s' in account '%s'.",
            region,
            current_aws_account_id,
        )
        stacks = get_cloudformation_stacks(boto3_session, region)
        stacks = transform_cloudformation_stacks(stacks)
        load_cloudformation_stacks(
            neo4j_session,
            stacks,
            region,
            current_aws_account_id,
            update_tag,
        )
    cleanup(neo4j_session, common_job_parameters)
