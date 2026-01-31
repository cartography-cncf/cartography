import logging
from typing import Any
from typing import Dict
from typing import List

import boto3
import botocore.exceptions
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.aws.ec2.util import get_botocore_config
from cartography.intel.aws.datapipeline_privilege_escalation import (
    create_datapipeline_can_exec_relationships,
    cleanup_datapipeline_can_exec_relationships,
)
from cartography.models.aws.datapipeline import DataPipelineSchema
from cartography.util import aws_handle_regions
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_datapipeline_pipelines(
    boto3_session: boto3.session.Session,
    region: str,
) -> List[Dict[str, Any]]:
    client = boto3_session.client(
        "datapipeline",
        region_name=region,
        config=get_botocore_config(),
    )
    pipelines: List[Dict[str, Any]] = []
    paginator = client.get_paginator("list_pipelines")
    try:
        for page in paginator.paginate():
            pipeline_ids = page.get("pipelineIdList", [])
            for pipeline_info in pipeline_ids:
                pipeline_id = pipeline_info["id"]
                pipeline_details = get_datapipeline_describe_pipeline(
                    boto3_session,
                    region,
                    pipeline_id,
                )
                if pipeline_details:
                    pipelines.append(pipeline_details)
    except botocore.exceptions.ClientError as e:
        code = e.response["Error"]["Code"]
        msg = e.response["Error"]["Message"]
        logger.warning(
            f"Could not run DataPipeline list_pipelines due to boto3 error {code}: {msg}. Skipping.",
        )
        return []

    return pipelines


@timeit
@aws_handle_regions
def get_datapipeline_describe_pipeline(
    boto3_session: boto3.session.Session,
    region: str,
    pipeline_id: str,
) -> Dict[str, Any]:
    client = boto3_session.client(
        "datapipeline",
        region_name=region,
        config=get_botocore_config(),
    )
    pipeline_details: Dict[str, Any] = {}
    try:
        response = client.describe_pipeline(pipelineId=pipeline_id)
        pipeline_description = response.get("pipelineDescription", {})

        # Extract the relevant fields
        pipeline_fields = pipeline_description.get("fields", [])
        pipeline_info = {
            "id": pipeline_description.get("pipelineId"),
            "name": "",
            "description": "",
            "state": "",
            "userId": "",
        }

        for field in pipeline_fields:
            key = field.get("key")
            value = field.get("stringValue", "")
            if key == "name":
                pipeline_info["name"] = value
            elif key == "description":
                pipeline_info["description"] = value
            elif key == "@state":
                pipeline_info["state"] = value
            elif key == "userId":
                pipeline_info["userId"] = value

        pipeline_details = pipeline_info
        return pipeline_details

    except botocore.exceptions.ClientError as e:
        code = e.response["Error"]["Code"]
        msg = e.response["Error"]["Message"]
        logger.warning(
            f"Could not run DataPipeline describe_pipeline for {pipeline_id} due to boto3 error {code}: {msg}. Skipping.",
        )
    return pipeline_details


@timeit
def load_datapipeline_pipelines(
    neo4j_session: neo4j.Session,
    pipeline_data: List[Dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    logger.info(
        f"Loading DataPipeline {len(pipeline_data)} pipelines for region '{region}' into graph.",
    )
    load(
        neo4j_session,
        DataPipelineSchema(),
        pipeline_data,
        lastupdated=aws_update_tag,
        Region=region,
        AWS_ID=current_aws_account_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict[str, Any],
) -> None:
    logger.debug("Running DataPipeline cleanup job.")
    cleanup_job = GraphJob.from_node_schema(DataPipelineSchema(), common_job_parameters)
    cleanup_job.run(neo4j_session)
    
    # Clean up custom Data Pipeline CAN_EXEC relationships
    cleanup_datapipeline_can_exec_relationships(neo4j_session, common_job_parameters.get("UPDATE_TAG", 0))


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
            f"Syncing DataPipeline for region '{region}' in account '{current_aws_account_id}'.",
        )

        pipelines = get_datapipeline_pipelines(boto3_session, region)

        load_datapipeline_pipelines(
            neo4j_session,
            pipelines,
            region,
            current_aws_account_id,
            update_tag,
        )

    cleanup(neo4j_session, common_job_parameters)
    
    # Run custom Data Pipeline privilege escalation analysis with AND logic
    logger.info("Running Data Pipeline privilege escalation analysis with AND logic")
    create_datapipeline_can_exec_relationships(neo4j_session)
