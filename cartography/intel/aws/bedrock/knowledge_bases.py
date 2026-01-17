"""
Intel module for AWS Bedrock Knowledge Bases.
Knowledge Bases provide RAG (Retrieval Augmented Generation) capabilities by sourcing
documents from S3, converting them to embeddings, and storing vectors for semantic search.
"""

import logging
from typing import Any
from typing import Dict
from typing import List

import boto3
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.aws.bedrock.knowledge_base import AWSBedrockKnowledgeBaseSchema
from cartography.util import aws_handle_regions
from cartography.util import timeit

from .util import get_botocore_config

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_knowledge_bases(
    boto3_session: boto3.session.Session, region: str
) -> List[Dict[str, Any]]:
    """
    Retrieve all knowledge bases in AWS Bedrock for a given region.
    """
    logger.info("Fetching Bedrock knowledge bases in region %s", region)
    client = boto3_session.client(
        "bedrock-agent",
        region_name=region,
        config=get_botocore_config(),
    )

    # List all knowledge bases (with pagination)
    paginator = client.get_paginator("list_knowledge_bases")
    kb_summaries = []
    for page in paginator.paginate():
        kb_summaries.extend(page.get("knowledgeBaseSummaries", []))

    logger.info(
        "Found %d knowledge base summaries in region %s", len(kb_summaries), region
    )

    # Get detailed information for each knowledge base
    knowledge_bases = []
    for summary in kb_summaries:
        kb_id = summary["knowledgeBaseId"]

        # Get knowledge base details
        kb_response = client.get_knowledge_base(knowledgeBaseId=kb_id)
        kb_details = kb_response.get("knowledgeBase", {})

        # Get data sources for S3 bucket relationships (with pagination)
        ds_paginator = client.get_paginator("list_data_sources")
        data_source_summaries = []
        for page in ds_paginator.paginate(knowledgeBaseId=kb_id):
            data_source_summaries.extend(page.get("dataSourceSummaries", []))

        # Get full details for each data source to extract S3 bucket ARN
        data_sources_with_details = []
        for ds_summary in data_source_summaries:
            ds_id = ds_summary["dataSourceId"]

            ds_details_response = client.get_data_source(
                knowledgeBaseId=kb_id,
                dataSourceId=ds_id,
            )
            data_source_details = ds_details_response.get("dataSource", {})
            data_sources_with_details.append(data_source_details)

        kb_details["dataSourceDetails"] = data_sources_with_details

        knowledge_bases.append(kb_details)

    logger.info(
        "Retrieved %d knowledge bases in region %s", len(knowledge_bases), region
    )

    return knowledge_bases


def transform_knowledge_bases(
    knowledge_bases: List[Dict[str, Any]], region: str
) -> List[Dict[str, Any]]:
    """
    Transform knowledge base data for ingestion into the graph.

    Extracts S3 bucket names from data sources and prepares embedding model ARN
    for relationship creation.
    """
    for kb in knowledge_bases:
        kb["Region"] = region

        # Extract embedding model ARN - it's already in the right format
        embedding_model_arn = (
            kb.get("knowledgeBaseConfiguration", {})
            .get("vectorKnowledgeBaseConfiguration", {})
            .get("embeddingModelArn")
        )
        if embedding_model_arn:
            kb["embeddingModelArn"] = embedding_model_arn

        # Extract S3 bucket names from data sources for [:SOURCES_DATA_FROM] relationship
        data_sources = kb.get("dataSourceDetails", [])
        if data_sources:
            bucket_names = []
            for ds in data_sources:
                s3_config = ds.get("dataSourceConfiguration", {}).get(
                    "s3Configuration", {}
                )
                bucket_arn = s3_config.get("bucketArn")
                if bucket_arn:
                    # Extract bucket name from ARN: arn:aws:s3:::bucket-name
                    bucket_name = bucket_arn.split(":::")[-1]
                    bucket_names.append(bucket_name)
            if bucket_names:
                kb["data_source_bucket_names"] = bucket_names

    return knowledge_bases


@timeit
def load_knowledge_bases(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    region: str,
    aws_account_id: str,
    update_tag: int,
) -> None:
    """
    Load knowledge bases into the graph database.
    """
    logger.info("Loading %d Bedrock knowledge bases for region %s", len(data), region)

    load(
        neo4j_session,
        AWSBedrockKnowledgeBaseSchema(),
        data,
        Region=region,
        AWS_ID=aws_account_id,
        lastupdated=update_tag,
    )


@timeit
def cleanup_knowledge_bases(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict,
) -> None:
    """
    Remove stale knowledge base nodes from the graph.
    """
    logger.info("Cleaning up stale Bedrock knowledge bases")

    GraphJob.from_node_schema(
        AWSBedrockKnowledgeBaseSchema(),
        common_job_parameters,
    ).run(neo4j_session)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: list[str],
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: Dict,
) -> None:
    """
    Sync AWS Bedrock Knowledge Bases across all specified regions.
    """
    logger.info(
        "Syncing Bedrock knowledge bases for account %s across %d regions",
        current_aws_account_id,
        len(regions),
    )

    for region in regions:
        # Fetch knowledge bases from AWS
        knowledge_bases = get_knowledge_bases(boto3_session, region)

        if not knowledge_bases:
            logger.info("No knowledge bases found in region %s", region)
            continue

        # Transform data for ingestion
        transformed_kbs = transform_knowledge_bases(knowledge_bases, region)

        # Load into Neo4j
        load_knowledge_bases(
            neo4j_session,
            transformed_kbs,
            region,
            current_aws_account_id,
            update_tag,
        )

    # Clean up stale nodes (once, after all regions)
    cleanup_knowledge_bases(neo4j_session, common_job_parameters)
