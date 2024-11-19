from collections import namedtuple
import logging

import boto3
import neo4j

from cartography.client.core.tx import load
from cartography.models.aws.ec2.auto_scaling_groups import AutoScalingGroupSchema, EC2InstanceAutoScalingGroupSchema, EC2SubnetAutoScalingGroupSchema
from cartography.models.aws.ec2.launch_configurations import LaunchConfigurationSchema

from .util import get_botocore_config
from cartography.util import aws_handle_regions
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)

AsgData = namedtuple(
    'AsgData', [
        "group_list",
        "instance_list",
        "subnet_list",
    ],
)


@timeit
@aws_handle_regions
def get_ec2_auto_scaling_groups(boto3_session: boto3.session.Session, region: str) -> list[dict]:
    client = boto3_session.client('autoscaling', region_name=region, config=get_botocore_config())
    paginator = client.get_paginator('describe_auto_scaling_groups')
    asgs: list[dict] = []
    for page in paginator.paginate():
        asgs.extend(page['AutoScalingGroups'])
    return asgs


@timeit
@aws_handle_regions
def get_launch_configurations(boto3_session: boto3.session.Session, region: str) -> list[dict]:
    client = boto3_session.client('autoscaling', region_name=region, config=get_botocore_config())
    paginator = client.get_paginator('describe_launch_configurations')
    lcs: list[dict] = []
    for page in paginator.paginate():
        lcs.extend(page['LaunchConfigurations'])
    return lcs


def transform_launch_configurations(configurations: list[dict[str, any]]):
    transformed_configurations = []
    for config in configurations:
        transformed_configurations.append({
            'LaunchConfigurationARN': config.get('LaunchConfigurationARN'),
            'CreatedTime': config.get('CreatedTime'),
            'ImageId': config.get('ImageId'),
            'KeyName': config.get('KeyName'),
            'SecurityGroups': config.get('SecurityGroups'),
            'InstanceType': config.get('InstanceType'),
            'KernelId': config.get('KernelId'),
            'RamdiskId': config.get('RamdiskId'),
            'InstanceMonitoring': config.get('InstanceMonitoring', {}).get('Enabled'),
            'SpotPrice': config.get('SpotPrice'),
            'IamInstanceProfile': config.get('IamInstanceProfile'),
            'EbsOptimized': config.get('EbsOptimized'),
            'AssociatePublicIpAddress': config.get('AssociatePublicIpAddress'),
            'PlacementTenancy': config.get('PlacementTenancy')
        })
    return transformed_configurations


def transform_auto_scaling_groups(groups: list[dict[str, any]]) -> AsgData:
    transformed_groups = []
    related_vpcs = []
    related_instances = []
    for group in groups:
        transformed_groups.append({
            'AutoScalingGroupARN': group.get('AutoScalingGroupARN'),
            'CapacityRebalance': group.get('CapacityRebalance'),
            'CreatedTime': str(group.get('CreatedTime')),
            'DefaultCooldown': group.get('DefaultCooldown'),
            'DesiredCapacity': group.get('DesiredCapacity'),
            'HealthCheckGracePeriod': group.get('HealthCheckGracePeriod'),
            'HealthCheckType': group.get('HealthCheckType'),
            'LaunchConfigurationName': group.get('LaunchConfigurationName'),
            'LaunchTemplateName': group.get('LaunchTemplate', {}).get('LaunchTemplateName'),
            'LaunchTemplateId': group.get('LaunchTemplate', {}).get('LaunchTemplateId'),
            'LaunchTemplateVersion': group.get('LaunchTemplate', {}).get('Version'),
            'MaxInstanceLifetime': group.get('MaxInstanceLifetime'),
            'MaxSize': group.get('MaxSize'),
            'MinSize': group.get('MinSize'),
            'AutoScalingGroupName': group.get('AutoScalingGroupName'),
            'NewInstancesProtectedFromScaleIn': group.get('NewInstancesProtectedFromScaleIn'),
            'Status': group.get('Status'),
            'AutoScalingGroupName': group.get('AutoScalingGroupName'),
        })

        if group.get('VPCZoneIdentifier', None):
            vpclist = group['VPCZoneIdentifier']
            subnet_ids = vpclist.split(',') if ',' in vpclist else [vpclist]
            data = [{'VPCZoneIdentifier': subnet_id} for subnet_id in subnet_ids]
            related_vpcs.extend(data)

        for instance_data in group.get('Instances', []):
            related_instances.append({'InstanceId': instance_data['InstanceId']})

    return AsgData(
        group_list=transformed_groups,
        instance_list=related_instances,
        subnet_list=related_vpcs
    )


@timeit
def load_launch_configurations(
    neo4j_session: neo4j.Session, data: list[dict], region: str, current_aws_account_id: str, update_tag: int
) -> None:
    load(
        neo4j_session,
        LaunchConfigurationSchema(),
        data,
        Region=region,
        AWS_ID=current_aws_account_id,
        update_tag=update_tag
    )


def load_groups(
        neo4j_session: neo4j.Session, data: list[dict], region: str, current_aws_account_id: str, update_tag: int
) -> None:
    load(
        neo4j_session,
        AutoScalingGroupSchema(),
        data,
        Region=region,
        AWS_ID=current_aws_account_id,
        update_tag=update_tag
    )


def load_vpcs(
        neo4j_session: neo4j.Session, data: list[dict], region: str, current_aws_account_id: str, update_tag: int
) -> None:
    load(
        neo4j_session,
        EC2SubnetAutoScalingGroupSchema(),
        data,
        Region=region,
        AWS_ID=current_aws_account_id,
        update_tag=update_tag
    )


def load_instances(
        neo4j_session: neo4j.Session, data: list[dict], region: str, current_aws_account_id: str, update_tag: int
) -> None:
    load(
        neo4j_session,
        EC2InstanceAutoScalingGroupSchema(),
        data,
        Region=region,
        AWS_ID=current_aws_account_id,
        update_tag=update_tag
    )

@timeit
def load_auto_scaling_groups(
    neo4j_session: neo4j.Session, data: AsgData, region: str, current_aws_account_id: str, update_tag: int
) -> None:
    load_auto_scaling_groups(neo4j_session, data.group_list, region, current_aws_account_id, update_tag)
    load_instances(neo4j_session, data.instance_list, region, current_aws_account_id, update_tag)
    load_vpcs(neo4j_session, data.subnet_list, region, current_aws_account_id, update_tag)

@timeit
def cleanup_ec2_auto_scaling_groups(neo4j_session: neo4j.Session, common_job_parameters: dict) -> None:
    run_cleanup_job(
        'aws_ingest_ec2_auto_scaling_groups_cleanup.json',
        neo4j_session,
        common_job_parameters,
    )


@timeit
def cleanup_ec2_launch_configurations(neo4j_session: neo4j.Session, common_job_parameters: dict) -> None:
    run_cleanup_job(
        'aws_import_ec2_launch_configurations_cleanup.json',
        neo4j_session,
        common_job_parameters,
    )


@timeit
def sync_ec2_auto_scaling_groups(
        neo4j_session: neo4j.Session, boto3_session: boto3.session.Session, regions: list[str],
        current_aws_account_id: str, update_tag: int, common_job_parameters: dict,
) -> None:
    for region in regions:
        logger.debug("Syncing auto scaling groups for region '%s' in account '%s'.", region, current_aws_account_id)
        lc_data = get_launch_configurations(boto3_session, region)
        asg_data = get_ec2_auto_scaling_groups(boto3_session, region)
        lc_transformed = transform_launch_configurations(lc_data)
        asg_transformed = transform_auto_scaling_groups(asg_data)
        load_launch_configurations(neo4j_session, lc_transformed, region, current_aws_account_id, update_tag)
        load_auto_scaling_groups(neo4j_session, asg_transformed, region, current_aws_account_id, update_tag)
    cleanup_ec2_auto_scaling_groups(neo4j_session, common_job_parameters)
    cleanup_ec2_launch_configurations(neo4j_session, common_job_parameters)
