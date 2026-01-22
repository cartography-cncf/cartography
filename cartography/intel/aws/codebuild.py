import logging
from typing import Any
from typing import Dict
from typing import List

import boto3
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.aws.ec2.util import get_botocore_config
from cartography.models.aws.codebuild.project import CodeBuildProjectSchema
from cartography.util import aws_handle_regions
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_all_codebuild_projects(
    boto3_session: boto3.Session, region: str
) -> List[Dict[str, Any]]:

    client = boto3_session.client(
        "codebuild", region_name=region, config=get_botocore_config()
    )
    paginator = client.get_paginator("list_projects")

    all_projects = []

    for page in paginator.paginate():
        project_names = page.get("projects", [])
        if not project_names:
            continue

        # AWS batch_get_projects accepts up to 100 project names per call as per AWS documentation.
        for i in range(0, len(project_names), 100):
            batch = project_names[i : i + 100]
            response = client.batch_get_projects(names=batch)
            projects = response.get("projects", [])
            all_projects.extend(projects)
    return all_projects


def transform_codebuild_projects(
    projects: List[Dict[str, Any]], region: str
) -> List[Dict[str, Any]]:
    """
    Transform CodeBuild project data for ingestion into Neo4j.

    - Includes all environment variable names.
    - Variables of type 'PLAINTEXT' retain their values.
    - Other types (e.g., 'PARAMETER_STORE', 'SECRETS_MANAGER') have their values redacted.
    """
    transformed_codebuild_projects = []
    for project in projects:
        env_vars = project.get("environment", {}).get("environmentVariables", [])
        env_var_strings = [
            f"{var.get('name')}={var.get('value') if var.get('type') == 'PLAINTEXT' else '<REDACTED>'}"
            for var in env_vars
        ]
        transformed_project = {
            "arn": project["arn"],
            "created": project.get("created"),
            "environmentVariables": env_var_strings,
            "sourceType": project.get("source", {}).get("type"),
            "sourceLocation": project.get("source", {}).get("location"),
        }
        transformed_codebuild_projects.append(transformed_project)

    return transformed_codebuild_projects


@timeit
def load_codebuild_projects(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    logger.info(
        f"Loading CodeBuild {len(data)} projects for region '{region}' into graph.",
    )
    load(
        neo4j_session,
        CodeBuildProjectSchema(),
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
    logger.debug("Running Efs cleanup job.")
    GraphJob.from_node_schema(CodeBuildProjectSchema(), common_job_parameters).run(
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
            f"Syncing CodeBuild for region '{region}' in account '{current_aws_account_id}'.",
        )

        projects = get_all_codebuild_projects(boto3_session, region)
        transformed_projects = transform_codebuild_projects(projects, region)

        load_codebuild_projects(
            neo4j_session,
            transformed_projects,
            region,
            current_aws_account_id,
            update_tag,
        )

    cleanup(neo4j_session, common_job_parameters)
