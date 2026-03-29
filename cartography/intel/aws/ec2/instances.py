import base64
import logging
import time
from collections import namedtuple
from typing import Any
from typing import Dict
from typing import List

import boto3
import neo4j
from botocore.exceptions import ClientError
from cloudconsolelink.clouds.aws import AWSLinker

from cartography.client.core.tx import load
from cartography.data.operating_systems import OPERATING_SYSTEMS
from cartography.graph.job import GraphJob
from cartography.intel.aws.ec2.util import get_botocore_config
from cartography.models.aws.ec2.instances import EC2InstanceSchema
from cartography.models.aws.ec2.keypairs import EC2KeyPairSchema
from cartography.models.aws.ec2.networkinterface_instance import EC2NetworkInterfaceInstanceSchema
from cartography.models.aws.ec2.reservations import EC2ReservationSchema
from cartography.models.aws.ec2.securitygroup_instance import EC2SecurityGroupInstanceSchema
from cartography.models.aws.ec2.subnet_instance import EC2SubnetInstanceSchema
from cartography.models.aws.ec2.volumes import EBSVolumeInstanceSchema
from cartography.util import aws_handle_regions
from cartography.util import timeit

aws_console_link = AWSLinker()

logger = logging.getLogger(__name__)
aws_console_link = AWSLinker()

Ec2Data = namedtuple(
    "Ec2Data",
    [
        "reservation_list",
        "instance_list",
        "subnet_list",
        "sg_list",
        "keypair_list",
        "network_interface_list",
        "instance_ebs_volumes_list",
    ],
)


@timeit
def get_ec2_images(boto3_session: boto3.session.Session, image_ids: List[str], region: str) -> Dict[str, Dict]:
    client = boto3_session.client("ec2", region_name=region, config=get_botocore_config())
    image_details = {}

    for i in range(0, len(image_ids), 1000):
        batch = image_ids[i: i + 1000]

        try:
            response = client.describe_images(ImageIds=batch)
            images = response.get("Image", [])
            image_details.update({image["ImageId"]: image for image in images})
        except ClientError as e:
            logger.error(f"Error fetching image details for batch {i // 1000 + 1}: {e}")
            continue

    return image_details


@timeit
@aws_handle_regions
def get_ec2_instances(boto3_session: boto3.session.Session, region: str) -> List[Dict]:
    client = boto3_session.client("ec2", region_name=region, config=get_botocore_config())
    reservations = []
    image_ids = []
    try:
        paginator = client.get_paginator("describe_instances")
        for page in paginator.paginate():
            reservations.extend(page["Reservations"])
            for reservation in page["Reservations"]:
                for instance in reservation["Instances"]:
                    image_id = instance.get("ImageId")
                    if image_id:
                        image_ids.append(image_id)

        image_details = get_ec2_images(boto3_session, list(set(image_ids)), region)

        for reservation in reservations:
            reservation["region"] = region
            for instance in reservation["Instances"]:
                image_id = instance.get("ImageId")

                if image_id and image_id in image_details:
                    instance["OSDetails"] = image_details[image_id]

    except ClientError as e:
        if (
            e.response["Error"]["Code"] == "AccessDeniedException" or
            e.response["Error"]["Code"] == "UnauthorizedOperation"
        ):
            logger.warning(
                "ec2:describe_security_groups failed with AccessDeniedException; continuing sync.",
                exc_info=True,
            )
        else:
            raise

    return reservations


@timeit
@aws_handle_regions
def get_roles_from_instance_profile(
    boto3_session: boto3.session.Session,
    region: str,
    instance_profile_id,
) -> List[Dict]:
    iam_client = boto3_session.client("iam", region_name=region, config=get_botocore_config())
    try:
        response = iam_client.get_instance_profile(InstanceProfileName=instance_profile_id)
        roles = response.get("InstanceProfile", {}).get("Roles", [])
        return roles
    except Exception as e:
        print(f"Error fetching roles: {e}")
        return []


@timeit
@aws_handle_regions
def get_instance_user_data(
    boto3_session: boto3.session.Session,
    region: str,
    instance_id,
) -> str:
    user_data = None
    ec2_client = boto3_session.client("ec2", region_name=region, config=get_botocore_config())
    try:
        response = ec2_client.describe_instance_attribute(InstanceId=instance_id, Attribute='userData')
        if 'UserData' in response and 'Value' in response.get('UserData', {}):
            user_data = base64.b64decode(response['UserData']['Value']).decode('utf-8')
            return user_data
        else:
            return None
    except Exception as e:
        print(f"Error fetching instance user data: {e}")
        return None


def transform_ec2_instances(
    boto3_session: boto3.session.Session,
    reservations: List[Dict[str, Any]],
    region: str,
    current_aws_account_id: str,
) -> Ec2Data:
    reservation_list = []
    instance_list = []
    subnet_list = []
    keypair_list = []
    sg_list = []
    network_interface_list = []
    instance_ebs_volumes_list = []

    for reservation in reservations:
        reservation_id = reservation["ReservationId"]
        reservation_list.append(
            {
                "RequesterId": reservation.get("RequesterId"),
                "ReservationId": reservation["ReservationId"],
                "OwnerId": reservation["OwnerId"],
            },
        )

        for instance in reservation["Instances"]:
            instance_id = instance["InstanceId"]
            ip_owner_id = (
                instance.get("NetworkInterfaces") or [{}]
            )[0].get("Association", {}).get("IpOwnerId")
            is_static_ip = False if ip_owner_id == "amazon" else True if ip_owner_id else None
            InstanceArn = f"arn:aws:ec2:{region}:{current_aws_account_id}:instance/{instance_id}"
            launch_time = instance.get("LaunchTime")
            launch_time_unix = str(time.mktime(launch_time.timetuple())) if launch_time else None
            user_data = get_instance_user_data(boto3_session, region, instance_id)

            iam_roles = []
            if "IamInstanceProfile" in instance:
                instance_profile_id = instance["IamInstanceProfile"]["Id"]
                iam_roles = get_roles_from_instance_profile(boto3_session, region, instance_profile_id)

                for role in iam_roles:
                    role["InstanceId"] = instance_id

            os_details = instance.get("OSDetails", {})
            platform = os_details.get("Platform", "Linux")
            architecture = os_details.get("Architecture", "Unknown")
            virtualization_type = os_details.get("VirtualizationType", "Unknown")
            hypervisor = os_details.get("Hypervisor", "Unknown")
            vm_os = "Unknown"
            image_description = os_details.get("Description", "").lower()

            if image_description:
                for op_system in OPERATING_SYSTEMS:
                    if op_system in image_description:
                        vm_os = op_system
                        break

            vm_os_version = os_details.get("Name", "Unknown")

            instance_list.append(
                {
                    "InstanceId": instance_id,
                    "ReservationId": reservation_id,
                    "PublicDnsName": instance.get("PublicDnsName"),
                    "PublicIpAddress": instance.get("PublicIpAddress"),
                    "Ipv6Address": instance.get("Ipv6Address"),
                    "PublicIpOwnerId": ip_owner_id,
                    "IsStaticIp": is_static_ip,
                    "PrivateIpAddress": instance.get("PrivateIpAddress"),
                    "ImageId": instance.get("ImageId"),
                    "InstanceType": instance.get("InstanceType"),
                    "IamInstanceProfile": instance.get("IamInstanceProfile", {}).get("Arn"),
                    "MonitoringState": instance.get("Monitoring", {}).get("State"),
                    "LaunchTime": instance.get("LaunchTime"),
                    "LaunchTimeUnix": launch_time_unix,
                    "State": instance.get("State", {}).get("Name"),
                    "AvailabilityZone": instance.get("Placement", {}).get("AvailabilityZone"),
                    "Tenancy": instance.get("Placement", {}).get("Tenancy"),
                    "HostResourceGroupArn": instance.get("Placement", {}).get("HostResourceGroupArn"),
                    "Platform": platform,
                    "Architecture": architecture,
                    "VirtualizationType": virtualization_type,
                    "Hypervisor": hypervisor,
                    "VmOs": vm_os,
                    "VmOsVersion": vm_os_version,
                    "EbsOptimized": instance.get("EbsOptimized"),
                    "BootMode": instance.get("BootMode"),
                    "InstanceLifecycle": instance.get("InstanceLifecycle"),
                    "HibernationOptions": instance.get("HibernationOptions", {}).get("Configured"),
                    "Region": region,
                    "consolelink'": aws_console_link.get_console_link(arn=InstanceArn),
                    "arn": InstanceArn,
                    "IamRoles": iam_roles,
                    "UserData": user_data,
                },
            )

            subnet_id = instance.get("SubnetId")
            if subnet_id:
                subnet_list.append(
                    {
                        "SubnetId": subnet_id,
                        "InstanceId": instance_id,
                    },
                )

            if instance.get("KeyName"):
                key_name = instance["KeyName"]
                key_pair_arn = f"arn:aws:ec2:{region}:{current_aws_account_id}:key-pair/{key_name}"
                keypair_list.append(
                    {
                        "KeyPairArn": key_pair_arn,
                        "KeyName": key_name,
                        "InstanceId": instance_id,
                    },
                )

            if instance.get("SecurityGroups"):
                for group in instance["SecurityGroups"]:
                    sg_list.append(
                        {
                            "GroupId": group["GroupId"],
                            "InstanceId": instance_id,
                        },
                    )

            for network_interface in instance["NetworkInterfaces"]:
                for security_group in network_interface.get("Groups", []):
                    network_interface_list.append(
                        {
                            "NetworkInterfaceId": network_interface["NetworkInterfaceId"],
                            "Status": network_interface["Status"],
                            "MacAddress": network_interface["MacAddress"],
                            "Description": network_interface["Description"],
                            "PrivateDnsName": network_interface.get("PrivateDnsName"),
                            "PrivateIpAddress": network_interface.get("PrivateIpAddress"),
                            "InstanceId": instance_id,
                            "SubnetId": subnet_id,
                            "GroupId": security_group["GroupId"],
                        },
                    )

            if "BlockDeviceMappings" in instance and len(instance["BlockDeviceMappings"]) > 0:
                for mapping in instance["BlockDeviceMappings"]:
                    if "VolumeId" in mapping["Ebs"]:
                        instance_ebs_volumes_list.append(
                            {
                                "InstanceId": instance_id,
                                "VolumeId": mapping["Ebs"]["VolumeId"],
                                "DeleteOnTermination": mapping["Ebs"]["DeleteOnTermination"],
                                # 'SnapshotId': mapping['Ebs']['SnapshotId'],  # TODO check on this
                            },
                        )

    return Ec2Data(
        reservation_list=reservation_list,
        instance_list=instance_list,
        subnet_list=subnet_list,
        sg_list=sg_list,
        keypair_list=keypair_list,
        network_interface_list=network_interface_list,
        instance_ebs_volumes_list=instance_ebs_volumes_list,
    )


@timeit
def load_ec2_reservations(
    neo4j_session: neo4j.Session,
    reservation_list: List[Dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        EC2ReservationSchema(),
        reservation_list,
        Region=region,
        AWS_ID=current_aws_account_id,
        lastupdated=update_tag,
    )


@timeit
def load_ec2_subnets(
    neo4j_session: neo4j.Session,
    subnet_list: List[Dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        EC2SubnetInstanceSchema(),
        subnet_list,
        Region=region,
        AWS_ID=current_aws_account_id,
        lastupdated=update_tag,
    )


@timeit
def load_ec2_key_pairs(
    neo4j_session: neo4j.Session,
    key_pair_list: List[Dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        EC2KeyPairSchema(),
        key_pair_list,
        Region=region,
        AWS_ID=current_aws_account_id,
        lastupdated=update_tag,
    )


@timeit
def load_ec2_security_groups(
    neo4j_session: neo4j.Session,
    sg_list: List[Dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        EC2SecurityGroupInstanceSchema(),
        sg_list,
        Region=region,
        AWS_ID=current_aws_account_id,
        lastupdated=update_tag,
    )


@timeit
def load_ec2_network_interfaces(
    neo4j_session: neo4j.Session,
    network_interface_list: List[Dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        EC2NetworkInterfaceInstanceSchema(),
        network_interface_list,
        Region=region,
        AWS_ID=current_aws_account_id,
        lastupdated=update_tag,
    )


@timeit
def load_ec2_instance_nodes(
    neo4j_session: neo4j.Session,
    data: List[Dict],
    region: str,
    current_aws_account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        EC2InstanceSchema(),
        data,
        Region=region,
        AWS_ID=current_aws_account_id,
        lastupdated=update_tag,
    )


@timeit
def load_ec2_instance_ebs_volumes(
    neo4j_session: neo4j.Session,
    ebs_data: List[Dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        EBSVolumeInstanceSchema(),
        ebs_data,
        Region=region,
        AWS_ID=current_aws_account_id,
        lastupdated=update_tag,
    )


# we will remove this logic whenever we are deploying to kubernetes


@timeit
def load_ec2_roles(
    neo4j_session: neo4j.Session,
    role_data: List[Dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    update_tag: int,
) -> None:
    ingest_role_instance_relations = """
    UNWIND $roles as role
    MATCH (instance:EC2Instance {id: role.InstanceId}), (roleNode:AWSRole {arn: role.Arn})
    MERGE (instance)-[r:USES]->(roleNode)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $aws_update_tag
    """

    neo4j_session.run(
        ingest_role_instance_relations,
        roles=role_data,
        aws_update_tag=update_tag,
    )


def load_ec2_instance_data(
    neo4j_session: neo4j.Session,
    region: str,
    current_aws_account_id: str,
    update_tag: int,
    reservation_list: List[Dict[str, Any]],
    instance_list: List[Dict[str, Any]],
    subnet_list: List[Dict[str, Any]],
    sg_list: List[Dict[str, Any]],
    key_pair_list: List[Dict[str, Any]],
    nic_list: List[Dict[str, Any]],
    ebs_volumes_list: List[Dict[str, Any]],
) -> None:
    role_data = [role for instance in instance_list for role in instance.get("IamRoles", [])]
    load_ec2_reservations(neo4j_session, reservation_list, region, current_aws_account_id, update_tag)
    load_ec2_instance_nodes(neo4j_session, instance_list, region, current_aws_account_id, update_tag)
    load_ec2_subnets(neo4j_session, subnet_list, region, current_aws_account_id, update_tag)
    load_ec2_security_groups(neo4j_session, sg_list, region, current_aws_account_id, update_tag)
    load_ec2_key_pairs(neo4j_session, key_pair_list, region, current_aws_account_id, update_tag)
    load_ec2_network_interfaces(neo4j_session, nic_list, region, current_aws_account_id, update_tag)
    load_ec2_instance_ebs_volumes(neo4j_session, ebs_volumes_list, region, current_aws_account_id, update_tag)
    load_ec2_roles(neo4j_session, role_data, region, current_aws_account_id, update_tag)


@timeit
def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]) -> None:
    logger.debug("Running EC2 instance cleanup")
    GraphJob.from_node_schema(EC2ReservationSchema(), common_job_parameters).run(neo4j_session)
    GraphJob.from_node_schema(EC2InstanceSchema(), common_job_parameters).run(neo4j_session)


@timeit
def sync_ec2_instances(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: List[str],
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:
    tic = time.perf_counter()
    for region in regions:
        logger.info("Syncing EC2 instances for region '%s' in account '%s'.", region, current_aws_account_id)
        reservations = get_ec2_instances(boto3_session, region)
        ec2_data = transform_ec2_instances(boto3_session, reservations, region, current_aws_account_id)
        load_ec2_instance_data(
            neo4j_session,
            region,
            current_aws_account_id,
            update_tag,
            ec2_data.reservation_list,
            ec2_data.instance_list,
            ec2_data.subnet_list,
            ec2_data.sg_list,
            ec2_data.keypair_list,
            ec2_data.network_interface_list,
            ec2_data.instance_ebs_volumes_list,
        )
    cleanup(neo4j_session, common_job_parameters)
    toc = time.perf_counter()
    logger.info(f"Time to process EC2 instances: {toc - tic:0.4f} seconds")
