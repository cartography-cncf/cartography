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
def get_codebuild_project_names(boto3_session: boto3.Session, region: str) -> List[str]:
    client = boto3_session.client(
        "codebuild", region_name=region, config=get_botocore_config()
    )
    paginator = client.get_paginator("list_projects")
    project_names = []
    for page in paginator.paginate():
        project_names.extend(page.get("projects", []))
    return project_names


@timeit
@aws_handle_regions
def get_codebuild_projects(
    boto3_session: boto3.Session, project_names: List[str], region: str
) -> List[Dict[str, Any]]:

    if not project_names:
        logger.debug(
            f"No CodeBuild projects found in region '{region}', skipping batch_get_projects call."
        )
        return []
    client = boto3_session.client(
        "codebuild", region_name=region, config=get_botocore_config()
    )
    response = client.batch_get_projects(names=project_names)
    return response.get("projects", [])


def transform_codebuild_projects(
    projects: List[Dict[str, Any]], region: str
) -> List[Dict[str, Any]]:
    """
    Transform CodeBuild project data for ingestion into Neo4j.

    - Only include environment variables of type 'PLAINTEXT'.
    - Other types (e.g., 'PARAMETER_STORE', 'SECRETS_MANAGER') are skipped to avoid leaking secrets.
    """
    transform_codebuild_projects = []
    for project in projects:
        env_vars = project.get("environment", {}).get("environmentVariables", [])
        env_var_strings = [
            f"{var.get('name')}={var.get('value')}"
            for var in env_vars
            if var.get("type") == "PLAINTEXT"
        ]
        transformed_project = {
            "arn": project["arn"],
            "created": project.get("created"),
            "environmentVariables": env_var_strings,
        }
        transform_codebuild_projects.append(transformed_project)

    return transform_codebuild_projects


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

        project_names = get_codebuild_project_names(boto3_session, region)
        projects = get_codebuild_projects(boto3_session, project_names, region)
        transformed_projects = transform_codebuild_projects(projects, region)

        load_codebuild_projects(
            neo4j_session,
            transformed_projects,
            region,
            current_aws_account_id,
            update_tag,
        )

    cleanup(neo4j_session, common_job_parameters)
