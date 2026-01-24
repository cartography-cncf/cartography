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
from cartography.models.aws.datapipeline import DataPipelineSchema
from cartography.util import aws_handle_regions
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_datapipeline_pipelines(
    boto3_session: boto3.session.Session,
    region: str,
) -> List[str]:
    """
    Get list of Data Pipeline IDs for a region.
    Returns list of pipeline IDs.
    """
    client = boto3_session.client(
        "datapipeline",
        region_name=region,
        config=get_botocore_config(),
    )
    pipeline_ids: List[str] = []
    try:
        paginator = client.get_paginator("list_pipelines")
        for page in paginator.paginate():
            pipelines = page.get("pipelineIdList", [])
            for pipeline in pipelines:
                pipeline_ids.append(pipeline["id"])
    except botocore.exceptions.ClientError as e:
        code = e.response["Error"]["Code"]
        msg = e.response["Error"]["Message"]
        logger.warning(
            f"Could not list Data Pipeline pipelines due to boto3 error {code}: {msg}. Skipping.",
        )
    return pipeline_ids


@timeit
def get_datapipeline_pipeline_details(
    boto3_session: boto3.session.Session,
    region: str,
    pipeline_ids: List[str],
) -> List[Dict[str, Any]]:
    """
    Get detailed information for Data Pipeline pipelines.
    AWS describe_pipelines accepts up to 25 pipeline IDs per call.
    """
    if not pipeline_ids:
        return []

    client = boto3_session.client(
        "datapipeline",
        region_name=region,
        config=get_botocore_config(),
    )
    pipeline_details: List[Dict[str, Any]] = []

    # AWS describe_pipelines accepts up to 25 pipeline IDs per call
    batch_size = 25
    for i in range(0, len(pipeline_ids), batch_size):
        batch = pipeline_ids[i : i + batch_size]
        try:
            response = client.describe_pipelines(pipelineIds=batch)
            pipelines = response.get("pipelineDescriptionList", [])
            pipeline_details.extend(pipelines)
        except botocore.exceptions.ClientError as e:
            code = e.response["Error"]["Code"]
            msg = e.response["Error"]["Message"]
            logger.warning(
                f"Could not describe Data Pipeline pipelines {batch} due to boto3 error {code}: {msg}. Skipping.",
            )

    return pipeline_details


@timeit
def transform_datapipeline_pipelines(
    pipeline_data: List[Dict[str, Any]],
    region: str,
) -> List[Dict[str, Any]]:
    """
    Transform Data Pipeline data for ingestion into Neo4j.
    """
    transformed_pipelines: List[Dict[str, Any]] = []
    for pipeline in pipeline_data:
        transformed_pipeline = {
            "pipelineId": pipeline.get("pipelineId"),
            "name": pipeline.get("name"),
            "description": pipeline.get("description"),
            "status": pipeline.get("pipelineState"),
        }
        transformed_pipelines.append(transformed_pipeline)
    return transformed_pipelines


@timeit
def load_datapipeline_pipelines(
    neo4j_session: neo4j.Session,
    pipeline_data: List[Dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    """
    Load Data Pipeline pipelines into Neo4j.
    """
    logger.info(
        f"Loading Data Pipeline {len(pipeline_data)} pipelines for region '{region}' into graph.",
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
    """
    Remove Data Pipeline pipelines that were not updated in this sync run.
    """
    logger.debug("Running Data Pipeline cleanup job.")
    cleanup_job = GraphJob.from_node_schema(DataPipelineSchema(), common_job_parameters)
    cleanup_job.run(neo4j_session)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: List[str],
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:
    """
    Sync Data Pipeline pipelines for the given regions.
    """
    for region in regions:
        logger.info(
            f"Syncing Data Pipeline for region '{region}' in account '{current_aws_account_id}'.",
        )

        # Get list of pipeline IDs
        pipeline_ids = get_datapipeline_pipelines(boto3_session, region)

        if not pipeline_ids:
            logger.info(f"No Data Pipeline pipelines found in region '{region}'.")
            continue

        # Get detailed information for pipelines
        pipeline_details = get_datapipeline_pipeline_details(
            boto3_session,
            region,
            pipeline_ids,
        )

        # Transform data for ingestion
        transformed_pipelines = transform_datapipeline_pipelines(
            pipeline_details,
            region,
        )

        # Load into Neo4j
        load_datapipeline_pipelines(
            neo4j_session,
            transformed_pipelines,
            region,
            current_aws_account_id,
            update_tag,
        )

    cleanup(neo4j_session, common_job_parameters)
