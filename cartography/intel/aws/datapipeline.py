import logging
from typing import Any

import boto3
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.aws.util.botocore_config import create_boto3_client
from cartography.intel.aws.util.botocore_config import get_botocore_config
from cartography.models.aws.datapipeline.pipeline import DataPipelineSchema
from cartography.util import aws_handle_regions
from cartography.util import timeit

logger = logging.getLogger(__name__)

DESCRIBE_PIPELINES_BATCH_SIZE = 25


def _build_datapipeline_arn(region: str, aws_account_id: str, pipeline_id: str) -> str:
    return f"arn:aws:datapipeline:{region}:{aws_account_id}:pipeline/{pipeline_id}"


def _get_pipeline_field_map(pipeline: dict[str, Any]) -> dict[str, Any]:
    field_map: dict[str, Any] = {}
    for field in pipeline.get("fields", []):
        key = field.get("key")
        if not key:
            continue
        field_map[key] = field.get("stringValue") or field.get("refValue")
    return field_map


@timeit
@aws_handle_regions
def get_datapipeline_pipelines(
    boto3_session: boto3.session.Session,
    region: str,
) -> list[dict[str, Any]]:
    client = create_boto3_client(
        boto3_session,
        "datapipeline",
        region_name=region,
        config=get_botocore_config(),
    )
    paginator = client.get_paginator("list_pipelines")
    pipelines: list[dict[str, Any]] = []
    for page in paginator.paginate():
        pipelines.extend(page.get("pipelineIdList", []))
    return pipelines


@timeit
@aws_handle_regions
def get_datapipeline_pipeline_details(
    boto3_session: boto3.session.Session,
    region: str,
    pipeline_summaries: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    pipeline_ids = [pipeline["id"] for pipeline in pipeline_summaries if pipeline.get("id")]
    if not pipeline_ids:
        return []

    client = create_boto3_client(
        boto3_session,
        "datapipeline",
        region_name=region,
        config=get_botocore_config(),
    )
    pipelines: list[dict[str, Any]] = []
    for i in range(0, len(pipeline_ids), DESCRIBE_PIPELINES_BATCH_SIZE):
        pipeline_ids_chunk = pipeline_ids[i : i + DESCRIBE_PIPELINES_BATCH_SIZE]
        response = client.describe_pipelines(pipelineIds=pipeline_ids_chunk)
        pipelines.extend(response.get("pipelineDescriptionList", []))
    return pipelines


def transform_datapipeline_pipelines(
    pipeline_details: list[dict[str, Any]],
    region: str,
    current_aws_account_id: str,
) -> list[dict[str, Any]]:
    transformed_pipelines: list[dict[str, Any]] = []
    for pipeline in pipeline_details:
        pipeline_id = pipeline.get("pipelineId")
        if not pipeline_id:
            continue

        field_map = _get_pipeline_field_map(pipeline)
        arn = _build_datapipeline_arn(region, current_aws_account_id, pipeline_id)
        transformed_pipelines.append(
            {
                "Id": arn,
                "Arn": arn,
                "PipelineId": pipeline_id,
                "Name": pipeline.get("name"),
                "Description": pipeline.get("description"),
                "UniqueId": pipeline.get("uniqueId"),
                "State": field_map.get("@pipelineState"),
                "HealthStatus": field_map.get("@healthStatus"),
                "Region": region,
            }
        )
    return transformed_pipelines


@timeit
def load_datapipeline_pipelines(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    logger.info(
        "Loading %d Data Pipeline resources for region '%s' into graph.",
        len(data),
        region,
    )
    load(
        neo4j_session,
        DataPipelineSchema(),
        data,
        Region=region,
        AWS_ID=current_aws_account_id,
        lastupdated=aws_update_tag,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    logger.debug("Running Data Pipeline cleanup job.")
    GraphJob.from_node_schema(DataPipelineSchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: list[str],
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    for region in regions:
        logger.info(
            "Syncing Data Pipeline for region '%s' in account '%s'.",
            region,
            current_aws_account_id,
        )

        pipeline_summaries = get_datapipeline_pipelines(boto3_session, region)
        pipeline_details = get_datapipeline_pipeline_details(
            boto3_session,
            region,
            pipeline_summaries,
        )
        transformed_pipelines = transform_datapipeline_pipelines(
            pipeline_details,
            region,
            current_aws_account_id,
        )
        load_datapipeline_pipelines(
            neo4j_session,
            transformed_pipelines,
            region,
            current_aws_account_id,
            update_tag,
        )

    cleanup(neo4j_session, common_job_parameters)
