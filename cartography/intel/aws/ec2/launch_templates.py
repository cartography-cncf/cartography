import logging
import time
from typing import Dict
from typing import List

import boto3
import neo4j
from cloudconsolelink.clouds.aws import AWSLinker

from .util import get_botocore_config
from cartography.util import aws_handle_regions
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)
aws_console_link = AWSLinker()


@timeit
@aws_handle_regions
def get_launch_templates(boto3_session: boto3.session.Session, region: str) -> List[Dict]:
    client = boto3_session.client('ec2', region_name=region, config=get_botocore_config())
    paginator = client.get_paginator('describe_launch_templates')
    templates: List[Dict] = []
    try:
        for page in paginator.paginate():
            templates.extend(page['LaunchTemplates'])

        for template in templates:
            template_versions: List[Dict] = []
            v_paginator = client.get_paginator('describe_launch_template_versions')
            for versions in v_paginator.paginate(LaunchTemplateId=template['LaunchTemplateId']):
                template_versions.extend(versions["LaunchTemplateVersions"])
            template["_template_versions"] = template_versions

    except Exception as e:
        logger.warning(f"Failed retrieve address for region - {region}. Error - {e}")

    return templates


@timeit
def load_launch_templates(
        neo4j_session: neo4j.Session, data: List[Dict], region: str, current_aws_account_id: str, update_tag: int,
) -> None:
    ingest_lt = """
    UNWIND $launch_templates as lt
        MERGE (template:LaunchTemplate{id: lt.LaunchTemplateId})
        ON CREATE SET template.firstseen = timestamp(),
        template.name = lt.LaunchTemplateName,
        template.create_time = lt.CreateTime,
        template.created_by = lt.CreatedBy
        SET template.default_version_number = lt.DefaultVersionNumber,
        template.latest_version_number = lt.LatestVersionNumber,
        template.lastupdated = $update_tag,
        template.region=$Region,
        template.consolelink = lt.consolelink
        WITH template, lt._template_versions as versions
        MATCH (aa:AWSAccount{id: $AWS_ACCOUNT_ID})
        MERGE (aa)-[r:RESOURCE]->(template)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $update_tag
        WITH template, versions
        UNWIND versions as tv
            MERGE (version:LaunchTemplateVersion{id: tv.LaunchTemplateId + '-' + tv.VersionNumber})
            ON CREATE SET version.firstseen = timestamp(),
            version.name = tv.LaunchTemplateName,
            version.create_time = tv.CreateTime,
            version.created_by = tv.CreatedBy,
            version.default_version = tv.DefaultVersion,
            version.version_number = tv.VersionNumber,
            version.version_description = tv.VersionDescription,
            version.kernel_id = tv.LaunchTemplateData.KernelId,
            version.ebs_optimized = tv.LaunchTemplateData.EbsOptimized,
            version.iam_instance_profile_arn = tv.LaunchTemplateData.IamInstanceProfile.Arn,
            version.iam_instance_profile_name = tv.LaunchTemplateData.IamInstanceProfile.Name,
            version.image_id = tv.LaunchTemplateData.ImageId,
            version.instance_type = tv.LaunchTemplateData.InstanceType,
            version.key_name = tv.LaunchTemplateData.KeyName,
            version.monitoring_enabled = tv.LaunchTemplateData.Monitoring.Enabled,
            version.ramdisk_id = tv.LaunchTemplateData.RamdiskId,
            version.disable_api_termination = tv.LaunchTemplateData.DisableApiTermination,
            version.instance_initiated_shutdown_behavior = tv.LaunchTemplateData.InstanceInitiatedShutdownBehavior,
            version.security_group_ids = tv.LaunchTemplateData.SecurityGroupIds,
            version.security_groups = tv.LaunchTemplateData.SecurityGroups
            SET version.lastupdated = $update_tag,
            version.region=$Region
            WITH template, version
            MERGE (template)-[r:VERSION]->(version)
            ON CREATE SET r.firstseen = timestamp()
            SET r.lastupdated = $update_tag
    """
    for lt in data:
        lt['CreateTime'] = str(time.mktime(lt['CreateTime'].timetuple()))
        arn = f"arn:aws:ec2:{region}:{current_aws_account_id}:launch-template/{lt['LaunchTemplateId']}"
        lt['consolelink'] = aws_console_link.get_console_link(arn=arn)
        for tv in lt.get("_template_versions", []):
            tv['CreateTime'] = str(time.mktime(tv['CreateTime'].timetuple()))

    neo4j_session.run(
        ingest_lt,
        launch_templates=data,
        AWS_ACCOUNT_ID=current_aws_account_id,
        Region=region,
        update_tag=update_tag,
    )


@timeit
def cleanup_ec2_launch_templates(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job(
        'aws_import_ec2_launch_templates_cleanup.json',
        neo4j_session,
        common_job_parameters,
    )


@timeit
def sync_ec2_launch_templates(
        neo4j_session: neo4j.Session, boto3_session: boto3.session.Session, regions: List[str],
        current_aws_account_id: str, update_tag: int, common_job_parameters: Dict,
) -> None:
    tic = time.perf_counter()

    logger.info("Syncing EC2 Launch Templates for account '%s', at %s.", current_aws_account_id, tic)

    for region in regions:
        logger.debug("Syncing launch templates for region '%s' in account '%s'.", region, current_aws_account_id)
        data = get_launch_templates(boto3_session, region)

        logger.info(f"Total EC2 Launch Templates: {len(data)} for {region}")

        load_launch_templates(neo4j_session, data, region, current_aws_account_id, update_tag)
    cleanup_ec2_launch_templates(neo4j_session, common_job_parameters)

    toc = time.perf_counter()
    logger.info(f"Time to process EC2 Launch Templates: {toc - tic:0.4f} seconds")
