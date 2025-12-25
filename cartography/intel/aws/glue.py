import logging
from typing import Any
from typing import Dict
from typing import List

import boto3
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.aws.ec2.util import get_botocore_config
from cartography.models.aws.glue.connection import GlueConnectionSchema
from cartography.models.aws.glue.database import AWSGlueDatabaseSchema
from cartography.models.aws.glue.job import GlueJobSchema
from cartography.util import aws_handle_regions
from cartography.util import dict_date_to_epoch
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_glue_connections(
    boto3_session: boto3.Session, region: str
) -> List[Dict[str, Any]]:
    client = boto3_session.client(
        "glue", region_name=region, config=get_botocore_config()
    )
    paginator = client.get_paginator("get_connections")
    connections = []
    for page in paginator.paginate():
        connections.extend(page.get("ConnectionList", []))

    return connections


@timeit
@aws_handle_regions
def get_glue_jobs(boto3_session: boto3.Session, region: str) -> List[Dict[str, Any]]:
    client = boto3_session.client(
        "glue", region_name=region, config=get_botocore_config()
    )
    paginator = client.get_paginator("get_jobs")
    jobs = []
    for page in paginator.paginate():
        jobs.extend(page.get("Jobs", []))
    return jobs


def transform_glue_job(jobs: List[Dict[str, Any]], region: str) -> List[Dict[str, Any]]:
    """
    Transform Glue job data for ingestion
    """
    transformed_jobs = []
    for job in jobs:
        transformed_job = {
            "Name": job["Name"],
            "ProfileName": job.get("ProfileName"),
            "JobMode": job.get("JobMode"),
            "Connections": job.get("Connections", {}).get("Connections"),
            "Region": region,
            "Description": job.get("Description"),
        }
        transformed_jobs.append(transformed_job)
    return transformed_jobs


def transform_glue_connections(
    connections: List[Dict[str, Any]], region: str
) -> List[Dict[str, Any]]:
    """
    Transform Glue connection data for ingestion
    """
    transformed_connections = []
    for connection in connections:
        transformed_connection = {
            "Name": connection["Name"],
            "Description": connection.get("Description"),
            "ConnectionType": connection.get("ConnectionType"),
            "Status": connection.get("Status"),
            "StatusReason": connection.get("StatusReason"),
            "AuthenticationType": connection.get("AuthenticationConfiguration", {}).get(
                "AuthenticationType"
            ),
            "SecretArn": connection.get("AuthenticationConfiguration", {}).get(
                "SecretArn"
            ),
            "Region": region,
        }
        transformed_connections.append(transformed_connection)
    return transformed_connections


@timeit
def load_glue_connections(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    logger.info(
        f"Loading Glue {len(data)} connections for region '{region}' into graph.",
    )
    load(
        neo4j_session,
        GlueConnectionSchema(),
        data,
        lastupdated=aws_update_tag,
        Region=region,
        AWS_ID=current_aws_account_id,
    )


@timeit
def load_glue_jobs(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    logger.info(
        f"Loading Glue {len(data)} jobs for region '{region}' into graph.",
    )
    load(
        neo4j_session,
        GlueJobSchema(),
        data,
        lastupdated=aws_update_tag,
        Region=region,
        AWS_ID=current_aws_account_id,
    )


@timeit
@aws_handle_regions
def get_glue_databases(
    boto3_session: boto3.Session, region: str
) -> List[Dict[str, Any]]:
    client = boto3_session.client(
        "glue", region_name=region, config=get_botocore_config()
    )
    databases = []
    paginator = client.get_paginator("get_databases")
    for page in paginator.paginate():
        databases.extend(page.get("DatabaseList", []))
    return databases


def transform_glue_databases(
    databases: List[Dict[str, Any]], region: str, current_aws_account_id: str
) -> List[Dict[str, Any]]:
    for db in databases:
        db["ARN"] = (
            f"arn:aws:glue:{region}:{current_aws_account_id}:database/{db['Name']}"
        )
        db["CreateTime"] = dict_date_to_epoch(db, "CreateTime")
    return databases


@timeit
def load_glue_databases(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    logger.info(f"Loading Glue {len(data)} databases for region '{region}' into graph.")
    load(
        neo4j_session,
        AWSGlueDatabaseSchema(),
        data,
        Region=region,
        AWS_ID=current_aws_account_id,
        lastupdated=aws_update_tag,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict[str, Any],
) -> None:
    logger.debug("Running Glue cleanup job.")
    GraphJob.from_node_schema(GlueConnectionSchema(), common_job_parameters).run(
        neo4j_session
    )
    GraphJob.from_node_schema(GlueJobSchema(), common_job_parameters).run(neo4j_session)
    GraphJob.from_node_schema(AWSGlueDatabaseSchema(), common_job_parameters).run(
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
            f"Syncing Glue for region '{region}' in account '{current_aws_account_id}'.",
        )

        connections = get_glue_connections(boto3_session, region)
        transformed_connections = transform_glue_connections(connections, region)
        load_glue_connections(
            neo4j_session,
            transformed_connections,
            region,
            current_aws_account_id,
            update_tag,
        )

        jobs = get_glue_jobs(boto3_session, region)
        transformed_jobs = transform_glue_job(jobs, region)
        load_glue_jobs(
            neo4j_session,
            transformed_jobs,
            region,
            current_aws_account_id,
            update_tag,
        )

        databases = get_glue_databases(boto3_session, region)
        transformed_databases = transform_glue_databases(
            databases, region, current_aws_account_id
        )
        load_glue_databases(
            neo4j_session,
            transformed_databases,
            region,
            current_aws_account_id,
            update_tag,
        )

    cleanup(neo4j_session, common_job_parameters)
