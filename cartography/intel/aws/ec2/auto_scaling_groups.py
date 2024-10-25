import logging
from typing import Dict
from typing import List

import boto3
import neo4j

from cartography.intel.aws.util.boto3 import get_botocore_config
from cartography.util import aws_handle_regions
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_ec2_auto_scaling_groups(boto3_session: boto3.session.Session, region: str) -> List[Dict]:
    client = boto3_session.client('autoscaling', region_name=region, config=get_botocore_config())
    paginator = client.get_paginator('describe_auto_scaling_groups')
    asgs: List[Dict] = []
    for page in paginator.paginate():
        asgs.extend(page['AutoScalingGroups'])
    return asgs


@timeit
@aws_handle_regions
def get_launch_configurations(boto3_session: boto3.session.Session, region: str) -> List[Dict]:
    client = boto3_session.client('autoscaling', region_name=region, config=get_botocore_config())
    paginator = client.get_paginator('describe_launch_configurations')
    lcs: List[Dict] = []
    for page in paginator.paginate():
        lcs.extend(page['LaunchConfigurations'])
    return lcs


@timeit
def load_launch_configurations(
        neo4j_session: neo4j.Session, data: List[Dict], region: str, current_aws_account_id: str, update_tag: int,
) -> None:
    ingest_lc = """
    UNWIND $launch_configurations as lc
        MERGE (config:LaunchConfiguration{id: lc.LaunchConfigurationARN})
        ON CREATE SET config.firstseen = timestamp(), config.name = lc.LaunchConfigurationName,
        config.arn = lc.LaunchConfigurationARN,
        config.created_time = lc.CreatedTime
        SET config.lastupdated = $update_tag, config.image_id = lc.ImageId,
        config.key_name = lc.KeyName,
        config.security_groups = lc.SecurityGroups,
        config.instance_type = lc.InstanceType,
        config.kernel_id = lc.KernelId,
        config.ramdisk_id = lc.RamdiskId,
        config.instance_monitoring_enabled = lc.InstanceMonitoring.Enabled,
        config.spot_price = lc.SpotPrice,
        config.iam_instance_profile = lc.IamInstanceProfile,
        config.ebs_optimized = lc.EbsOptimized,
        config.associate_public_ip_address = lc.AssociatePublicIpAddress,
        config.placement_tenancy = lc.PlacementTenancy,
        config.region=$Region
        WITH config
        MATCH (aa:AWSAccount{id: $AWS_ACCOUNT_ID})
        MERGE (aa)-[r:RESOURCE]->(config)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $update_tag
    """
    for lc in data:
        lc['CreatedTime'] = str(int(lc['CreatedTime'].timestamp()))

    neo4j_session.run(
        ingest_lc,
        launch_configurations=data,
        AWS_ACCOUNT_ID=current_aws_account_id,
        Region=region,
        update_tag=update_tag,
    )


@timeit
def load_ec2_auto_scaling_groups(
        neo4j_session: neo4j.Session, data: List[Dict], region: str, current_aws_account_id: str, update_tag: int,
) -> None:
    ingest_group = """
    UNWIND $autoscaling_groups_list as ag
        MERGE (group:AutoScalingGroup{arn: ag.AutoScalingGroupARN})
        ON CREATE SET group.firstseen = timestamp(),
        group.createdtime = ag.CreatedTime
        SET group.launchconfigurationname = ag.LaunchConfigurationName,
        group.launchtemplatename = ag.LaunchTemplate.LaunchTemplateName,
        group.launchtemplateid = ag.LaunchTemplate.LaunchTemplateId,
        group.launchtemplateversion = ag.LaunchTemplate.Version,
        group.maxsize = ag.MaxSize, group.minsize = ag.MinSize, group.defaultcooldown = ag.DefaultCooldown,
        group.desiredcapacity = ag.DesiredCapacity, group.healthchecktype = ag.HealthCheckType,
        group.healthcheckgraceperiod = ag.HealthCheckGracePeriod, group.status = ag.Status,
        group.newinstancesprotectedfromscalein = ag.NewInstancesProtectedFromScaleIn,
        group.maxinstancelifetime = ag.MaxInstanceLifetime, group.capacityrebalance = ag.CapacityRebalance,
        group.name = ag.AutoScalingGroupName,
        group.lastupdated = $update_tag,
        group.region=$Region
        WITH group
        MATCH (aa:AWSAccount{id: $AWS_ACCOUNT_ID})
        MERGE (aa)-[r:RESOURCE]->(group)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $update_tag
    """

    ingest_vpc = """
    UNWIND $vpc_id_list as vpc_id
        MERGE (subnet:EC2Subnet{subnetid: vpc_id})
        ON CREATE SET subnet.firstseen = timestamp()
        SET subnet.lastupdated = $update_tag
        WITH subnet
        MATCH (group:AutoScalingGroup{arn: $GROUPARN})
        MERGE (subnet)<-[r:VPC_IDENTIFIER]-(group)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $update_tag
    """

    ingest_instance = """
    UNWIND $instances_list as i
        MERGE (instance:Instance:EC2Instance{id: i.InstanceId})
        ON CREATE SET instance.firstseen = timestamp()
        SET instance.lastupdated = $update_tag, instance.region=$Region
        WITH instance
        MATCH (group:AutoScalingGroup{arn: $GROUPARN})
        MERGE (instance)-[r:MEMBER_AUTO_SCALE_GROUP]->(group)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $update_tag
        WITH instance
        MATCH (aa:AWSAccount{id: $AWS_ACCOUNT_ID})
        MERGE (aa)-[r:RESOURCE]->(instance)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $update_tag
    """

    ingest_lts = """
    UNWIND $autoscaling_groups_list as ag
        MATCH (group:AutoScalingGroup{arn: ag.AutoScalingGroupARN})
        MATCH (template:LaunchTemplate{id: ag.LaunchTemplate.LaunchTemplateId})
        MERGE (group)-[r:HAS_LAUNCH_TEMPLATE]->(template)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $update_tag
    """

    ingest_lcs = """
    UNWIND $autoscaling_groups_list as ag
        MATCH (group:AutoScalingGroup{arn: ag.AutoScalingGroupARN})
        MATCH (config:LaunchConfiguration{name: ag.LaunchConfigurationName})
        MERGE (group)-[r:HAS_LAUNCH_CONFIG]->(config)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $update_tag
    """

    launch_configs = []
    launch_templates = []
    for group in data:
        if group.get('LaunchConfigurationName'):
            launch_configs.append(group)
        if group.get('LaunchTemplate'):
            launch_templates.append(group)

        group['CreatedTime'] = str(group['CreatedTime'])

    neo4j_session.run(
        ingest_group,
        autoscaling_groups_list=data,
        AWS_ACCOUNT_ID=current_aws_account_id,
        Region=region,
        update_tag=update_tag,
    )
    neo4j_session.run(
        ingest_lcs,
        autoscaling_groups_list=launch_configs,
        AWS_ACCOUNT_ID=current_aws_account_id,
        Region=region,
        update_tag=update_tag,
    )
    neo4j_session.run(
        ingest_lts,
        autoscaling_groups_list=launch_templates,
        AWS_ACCOUNT_ID=current_aws_account_id,
        Region=region,
        update_tag=update_tag,
    )

    for group in data:
        group_arn = group["AutoScalingGroupARN"]
        if group.get('VPCZoneIdentifier'):
            vpclist = group["VPCZoneIdentifier"]
            if ',' in vpclist:
                data = vpclist.split(',')
            else:
                data = vpclist
            neo4j_session.run(
                ingest_vpc,
                vpc_id_list=data,
                GROUPARN=group_arn,
                update_tag=update_tag,
            )

        if group.get("Instances"):
            data = group["Instances"]
            neo4j_session.run(
                ingest_instance,
                instances_list=data,
                GROUPARN=group_arn,
                AWS_ACCOUNT_ID=current_aws_account_id,
                Region=region,
                update_tag=update_tag,
            )


@timeit
def cleanup_ec2_auto_scaling_groups(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job(
        'aws_ingest_ec2_auto_scaling_groups_cleanup.json',
        neo4j_session,
        common_job_parameters,
    )


@timeit
def cleanup_ec2_launch_configurations(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job(
        'aws_import_ec2_launch_configurations_cleanup.json',
        neo4j_session,
        common_job_parameters,
    )


@timeit
def sync_ec2_auto_scaling_groups(
        neo4j_session: neo4j.Session, boto3_session: boto3.session.Session, regions: List[str],
        current_aws_account_id: str, update_tag: int, common_job_parameters: Dict,
) -> None:
    for region in regions:
        logger.debug("Syncing auto scaling groups for region '%s' in account '%s'.", region, current_aws_account_id)
        lc_data = get_launch_configurations(boto3_session, region)
        load_launch_configurations(neo4j_session, lc_data, region, current_aws_account_id, update_tag)
        data = get_ec2_auto_scaling_groups(boto3_session, region)
        load_ec2_auto_scaling_groups(neo4j_session, data, region, current_aws_account_id, update_tag)
    cleanup_ec2_auto_scaling_groups(neo4j_session, common_job_parameters)
    cleanup_ec2_launch_configurations(neo4j_session, common_job_parameters)
