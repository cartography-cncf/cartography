import logging
from typing import Any

import boto3
import botocore
import neo4j

from .util import get_botocore_config
from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.aws.ec2.launch_template_versions import LaunchTemplateVersionSchema
from cartography.models.aws.ec2.launch_templates import LaunchTemplateSchema
from cartography.util import aws_handle_regions
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_launch_templates(
    boto3_session: boto3.session.Session,
    region: str,
) -> list[dict[str, Any]]:
    client = boto3_session.client('ec2', region_name=region, config=get_botocore_config())
    paginator = client.get_paginator('describe_launch_templates')
    templates: list[dict[str, Any]] = []
    for page in paginator.paginate():
        paginated_templates = page['LaunchTemplates']
        templates.extend(paginated_templates)
    return templates


@timeit
@aws_handle_regions
def get_launch_template_versions(
    boto3_session: boto3.session.Session,
    region: str,
    launch_templates: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    found_versions: list[dict[str, Any]] = []
    found_templates: list[dict[str, Any]] = []
    for template in launch_templates:
        launch_template_id = template['LaunchTemplateId']
        try:
            versions = get_launch_template_versions_by_template(
                boto3_session,
                launch_template_id,
                region,
            )
            # If the call succeeded, the template still exists.
            # Add it and its versions (list might be empty if no versions exist).
            found_templates.append(template)
            found_versions.extend(versions)
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'InvalidLaunchTemplateId.NotFound':
                logger.warning(
                    "Launch template %s no longer exists in region %s, skipping.",
                    launch_template_id, region,
                )
                # Skip this template, don't add it or its versions
                continue
            else:
                # Re-raise any other client error
                raise

    return found_versions, found_templates


@timeit
def get_launch_template_versions_by_template(
        boto3_session: boto3.session.Session,
        launch_template_id: str,
        region: str,
) -> list[dict[str, Any]]:
    client = boto3_session.client('ec2', region_name=region, config=get_botocore_config())
    v_paginator = client.get_paginator('describe_launch_template_versions')
    template_versions = []
    for versions_page in v_paginator.paginate(LaunchTemplateId=launch_template_id):
        template_versions.extend(versions_page['LaunchTemplateVersions'])
    return template_versions


def transform_launch_templates(templates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for template in templates:
        current = template.copy()
        current['CreateTime'] = str(int(current['CreateTime'].timestamp()))
        result.append(current)
    return result


@timeit
def load_launch_templates(
        neo4j_session: neo4j.Session,
        data: list[dict[str, Any]],
        region: str,
        current_aws_account_id: str,
        update_tag: int,
) -> None:
    load(
        neo4j_session,
        LaunchTemplateSchema(),
        data,
        Region=region,
        AWS_ID=current_aws_account_id,
        lastupdated=update_tag,
    )


def transform_launch_template_versions(versions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for version in versions:
        current = version.copy()

        # Reformat some fields
        current['Id'] = f"{version['LaunchTemplateId']}-{version['VersionNumber']}"
        current['CreateTime'] = str(int(version['CreateTime'].timestamp()))

        # Handle the nested object returned from boto
        ltd = version['LaunchTemplateData']
        current['KernelId'] = ltd.get('KernelId')
        current['EbsOptimized'] = ltd.get('EbsOptimized')
        current['IamInstanceProfileArn'] = ltd.get('IamInstanceProfileArn')
        current['IamInstanceProfileName'] = ltd.get('IamInstanceProfileName')
        current['ImageId'] = ltd.get('ImageId')
        current['InstanceType'] = ltd.get('InstanceType')
        current['KeyName'] = ltd.get('KeyName')
        current['MonitoringEnabled'] = ltd.get('MonitoringEnabled')
        current['RamdiskId'] = ltd.get('RamdiskId')
        current['DisableApiTermination'] = ltd.get('DisableApiTermination')
        current['InstanceInitiatedShutDownBehavior'] = ltd.get('InstanceInitiatedShutDownBehavior')
        current['SecurityGroupIds'] = ltd.get('SecurityGroupIds')
        current['SecurityGroups'] = ltd.get('SecurityGroups')
        result.append(current)
    return result


@timeit
def load_launch_template_versions(
        neo4j_session: neo4j.Session,
        data: list[dict[str, Any]],
        region: str,
        current_aws_account_id: str,
        update_tag: int,
) -> None:
    load(
        neo4j_session,
        LaunchTemplateVersionSchema(),
        data,
        Region=region,
        AWS_ID=current_aws_account_id,
        lastupdated=update_tag,
    )


@timeit
def cleanup(neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]) -> None:
    logger.info("Running launch template cleanup job.")
    cleanup_job = GraphJob.from_node_schema(LaunchTemplateSchema(), common_job_parameters)
    cleanup_job.run(neo4j_session)

    cleanup_job = GraphJob.from_node_schema(LaunchTemplateVersionSchema(), common_job_parameters)
    cleanup_job.run(neo4j_session)


@timeit
def sync_ec2_launch_templates(
        neo4j_session: neo4j.Session,
        boto3_session: boto3.session.Session,
        regions: list[str],
        current_aws_account_id: str,
        update_tag: int,
        common_job_parameters: dict[str, Any],
) -> None:
    for region in regions:
        logger.info(f"Syncing launch templates for region '{region}' in account '{current_aws_account_id}'.")
        templates = get_launch_templates(boto3_session, region)
        versions, found_templates = get_launch_template_versions(boto3_session, region, templates)

        # Transform and load only the templates that were found to exist
        transformed_templates = transform_launch_templates(found_templates)
        load_launch_templates(neo4j_session, transformed_templates, region, current_aws_account_id, update_tag)
        transformed_versions = transform_launch_template_versions(versions)
        load_launch_template_versions(neo4j_session, transformed_versions, region, current_aws_account_id, update_tag)

    cleanup(neo4j_session, common_job_parameters)
