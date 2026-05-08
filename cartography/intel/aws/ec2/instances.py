import logging
import time
from collections import namedtuple
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

import boto3
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.aws.util.botocore_config import create_boto3_client
from cartography.intel.aws.util.botocore_config import get_botocore_config
from cartography.models.aws.ec2.auto_scaling_groups import (
    EC2InstanceAutoScalingGroupSchema,
)
from cartography.models.aws.ec2.instances import EC2InstanceSchema
from cartography.models.aws.ec2.ipv6_addresses import EC2Ipv6AddressSchema
from cartography.models.aws.ec2.keypair_instance import EC2KeyPairInstanceSchema
from cartography.models.aws.ec2.networkinterface_instance import (
    EC2NetworkInterfaceInstanceSchema,
)
from cartography.models.aws.ec2.reservations import EC2ReservationSchema
from cartography.models.aws.ec2.securitygroup_instance import (
    EC2SecurityGroupInstanceSchema,
)
from cartography.models.aws.ec2.subnet_instance import EC2SubnetInstanceSchema
from cartography.models.aws.ec2.volumes import EBSVolumeInstanceSchema
from cartography.util import aws_handle_regions
from cartography.util import timeit

logger = logging.getLogger(__name__)

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
        "ipv6_address_list",
    ],
)


def _get_eks_cluster_name(tags: List[Dict[str, str]]) -> Optional[str]:
    for tag in tags:
        key = tag.get("Key")
        value = tag.get("Value")

        if key == "eks:cluster-name" and value:
            return value

        if key == "alpha.eksctl.io/cluster-name" and value:
            return value

        if key and key.startswith("kubernetes.io/cluster/"):
            cluster_name = key.split("kubernetes.io/cluster/")[-1]
            if cluster_name:
                return cluster_name

    return None


def _transform_metadata_options(metadata_options: Dict[str, Any]) -> Dict[str, Any]:
    http_tokens = metadata_options.get("HttpTokens")
    if http_tokens == "required":
        imds_access_mode = "v2_only"
    elif http_tokens == "optional":
        imds_access_mode = "v1_or_v2"
    else:
        imds_access_mode = None

    return {
        "MetadataHttpTokens": http_tokens,
        "MetadataHttpPutResponseHopLimit": metadata_options.get(
            "HttpPutResponseHopLimit",
        ),
        "MetadataHttpEndpoint": metadata_options.get("HttpEndpoint"),
        "MetadataHttpProtocolIpv6": metadata_options.get("HttpProtocolIpv6"),
        "MetadataInstanceTags": metadata_options.get("InstanceMetadataTags"),
        "ImdsAccessMode": imds_access_mode,
        "ImdsV1Enabled": http_tokens == "optional" if http_tokens else None,
        "ImdsV2Required": http_tokens == "required" if http_tokens else None,
    }


@timeit
@aws_handle_regions
def get_ec2_instances(boto3_session: boto3.session.Session, region: str) -> List[Dict]:
    client = create_boto3_client(
        boto3_session,
        "ec2",
        region_name=region,
        config=get_botocore_config(),
    )
    paginator = client.get_paginator("describe_instances")
    reservations: List[Dict[str, Any]] = []
    for page in paginator.paginate():
        reservations.extend(page["Reservations"])
    return reservations


def transform_ec2_instances(
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
    ipv6_address_list = []

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
            launch_time = instance.get("LaunchTime")
            launch_time_unix = (
                str(time.mktime(launch_time.timetuple())) if launch_time else None
            )
            eks_cluster_name = _get_eks_cluster_name(instance.get("Tags", []))

            # --- Extract primary IPv6 address for this instance ---
            # AWS does not surface IPv6 at the top-level instance object; it is
            # only available under NetworkInterfaces[].Ipv6Addresses[]. We look
            # at the NI with Attachment.DeviceIndex == 0 (the primary interface),
            # prefer the entry with IsPrimaryIpv6=True, and fall back to the first
            # entry in the list. If the primary NI has no IPv6, this is None.
            primary_ipv6 = None
            for nic in instance.get("NetworkInterfaces", []):
                if nic.get("Attachment", {}).get("DeviceIndex") == 0:
                    ipv6_list = nic.get("Ipv6Addresses", [])
                    if ipv6_list:
                        primary_entry = next(
                            (a for a in ipv6_list if a.get("IsPrimaryIpv6")),
                            ipv6_list[0],
                        )
                        primary_ipv6 = primary_entry.get("Ipv6Address")
                    break

            metadata_options = _transform_metadata_options(
                instance.get("MetadataOptions", {}),
            )
            instance_list.append(
                {
                    "InstanceId": instance_id,
                    "ReservationId": reservation_id,
                    "PublicDnsName": instance.get("PublicDnsName"),
                    "PublicIpAddress": instance.get("PublicIpAddress"),
                    "PrivateIpAddress": instance.get("PrivateIpAddress"),
                    "ImageId": instance.get("ImageId"),
                    "InstanceType": instance.get("InstanceType"),
                    "IamInstanceProfile": instance.get("IamInstanceProfile", {}).get(
                        "Arn",
                    ),
                    "MonitoringState": instance.get("Monitoring", {}).get("State"),
                    "LaunchTime": instance.get("LaunchTime"),
                    "LaunchTimeUnix": launch_time_unix,
                    "State": instance.get("State", {}).get("Name"),
                    "AvailabilityZone": instance.get("Placement", {}).get(
                        "AvailabilityZone",
                    ),
                    "Tenancy": instance.get("Placement", {}).get("Tenancy"),
                    "HostResourceGroupArn": instance.get("Placement", {}).get(
                        "HostResourceGroupArn",
                    ),
                    "Platform": instance.get("Platform"),
                    "Architecture": instance.get("Architecture"),
                    "EbsOptimized": instance.get("EbsOptimized"),
                    "BootMode": instance.get("BootMode"),
                    "InstanceLifecycle": instance.get("InstanceLifecycle"),
                    "HibernationOptions": instance.get("HibernationOptions", {}).get(
                        "Configured",
                    ),
                    **metadata_options,
                    "EksClusterName": eks_cluster_name,
                    "IPv6Address": primary_ipv6,
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
                key_pair_arn = (
                    f"arn:aws:ec2:{region}:{current_aws_account_id}:key-pair/{key_name}"
                )
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
                            "NetworkInterfaceId": network_interface[
                                "NetworkInterfaceId"
                            ],
                            "Status": network_interface["Status"],
                            "MacAddress": network_interface["MacAddress"],
                            "Description": network_interface["Description"],
                            "PrivateDnsName": network_interface.get("PrivateDnsName"),
                            "PrivateIpAddress": network_interface.get(
                                "PrivateIpAddress"
                            ),
                            "InstanceId": instance_id,
                            "SubnetId": subnet_id,
                            "GroupId": security_group["GroupId"],
                        },
                    )

                # --- Extract IPv6 addresses for this network interface ---
                # Each NI can have zero or more IPv6 addresses. We create a
                # separate EC2Ipv6Address node per address so they can be
                # independently queried and linked to DNS AAAA records via the
                # Ip label on EC2Ipv6Address and the existing DNS_POINTS_TO rel.
                nic_id = network_interface["NetworkInterfaceId"]
                for ipv6_entry in network_interface.get("Ipv6Addresses", []):
                    ipv6_addr = ipv6_entry.get("Ipv6Address")
                    if ipv6_addr:
                        ipv6_address_list.append(
                            {
                                "Ipv6Address": ipv6_addr,
                                "NetworkInterfaceId": nic_id,
                                # IsPrimaryIpv6 may be absent on older API versions;
                                # default to False rather than None for clean bool storage.
                                "IsPrimaryIpv6": ipv6_entry.get("IsPrimaryIpv6", False),
                            },
                        )

            if (
                "BlockDeviceMappings" in instance
                and len(instance["BlockDeviceMappings"]) > 0
            ):
                for mapping in instance["BlockDeviceMappings"]:
                    if "VolumeId" in mapping["Ebs"]:
                        instance_ebs_volumes_list.append(
                            {
                                "InstanceId": instance_id,
                                "VolumeId": mapping["Ebs"]["VolumeId"],
                                "DeleteOnTermination": mapping["Ebs"][
                                    "DeleteOnTermination"
                                ],
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
        ipv6_address_list=ipv6_address_list,
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
def load_ec2_keypair_instances(
    neo4j_session: neo4j.Session,
    key_pair_list: List[Dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    update_tag: int,
) -> None:
    # Load EC2 keypairs as known by describe-instances.
    load(
        neo4j_session,
        EC2KeyPairInstanceSchema(),
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


@timeit
def load_ec2_ipv6_addresses(
    neo4j_session: neo4j.Session,
    ipv6_address_list: List[Dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        EC2Ipv6AddressSchema(),
        ipv6_address_list,
        Region=region,
        AWS_ID=current_aws_account_id,
        lastupdated=update_tag,
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
    ipv6_address_list: List[Dict[str, Any]],
) -> None:
    load_ec2_reservations(
        neo4j_session,
        reservation_list,
        region,
        current_aws_account_id,
        update_tag,
    )
    load_ec2_instance_nodes(
        neo4j_session,
        instance_list,
        region,
        current_aws_account_id,
        update_tag,
    )
    load_ec2_subnets(
        neo4j_session,
        subnet_list,
        region,
        current_aws_account_id,
        update_tag,
    )
    load_ec2_security_groups(
        neo4j_session,
        sg_list,
        region,
        current_aws_account_id,
        update_tag,
    )
    load_ec2_keypair_instances(
        neo4j_session,
        key_pair_list,
        region,
        current_aws_account_id,
        update_tag,
    )
    load_ec2_network_interfaces(
        neo4j_session,
        nic_list,
        region,
        current_aws_account_id,
        update_tag,
    )
    load_ec2_instance_ebs_volumes(
        neo4j_session,
        ebs_volumes_list,
        region,
        current_aws_account_id,
        update_tag,
    )
    load_ec2_ipv6_addresses(
        neo4j_session,
        ipv6_address_list,
        region,
        current_aws_account_id,
        update_tag,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict[str, Any],
) -> None:
    logger.debug("Running EC2 instance cleanup")
    GraphJob.from_node_schema(EC2ReservationSchema(), common_job_parameters).run(
        neo4j_session,
    )
    GraphJob.from_node_schema(EC2InstanceSchema(), common_job_parameters).run(
        neo4j_session,
    )
    GraphJob.from_node_schema(
        EC2InstanceAutoScalingGroupSchema(),
        common_job_parameters,
    ).run(neo4j_session)
    GraphJob.from_node_schema(EC2Ipv6AddressSchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def sync_ec2_instances(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: List[str],
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:
    for region in regions:
        logger.info(
            "Syncing EC2 instances for region '%s' in account '%s'.",
            region,
            current_aws_account_id,
        )
        reservations = get_ec2_instances(boto3_session, region)
        ec2_data = transform_ec2_instances(reservations, region, current_aws_account_id)
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
            ec2_data.ipv6_address_list,
        )
    cleanup(neo4j_session, common_job_parameters)
