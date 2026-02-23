from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class EC2InstanceNodeProperties(CartographyNodeProperties):
    # TODO arn: PropertyRef = PropertyRef('Arn', extra_index=True)
    id: PropertyRef = PropertyRef("InstanceId")
    instanceid: PropertyRef = PropertyRef("InstanceId", extra_index=True)
    publicdnsname: PropertyRef = PropertyRef("PublicDnsName", extra_index=True)
    privateipaddress: PropertyRef = PropertyRef("PrivateIpAddress")
    publicipaddress: PropertyRef = PropertyRef("PublicIpAddress")
    ipv6address: PropertyRef = PropertyRef("Ipv6Address")
    publicipownerid: PropertyRef = PropertyRef("PublicIpOwnerId")
    isstaticip: PropertyRef = PropertyRef("IsStaticIp")
    imageid: PropertyRef = PropertyRef("ImageId")
    instancetype: PropertyRef = PropertyRef("InstanceType")
    monitoringstate: PropertyRef = PropertyRef("MonitoringState")
    state: PropertyRef = PropertyRef("State")
    launchtime: PropertyRef = PropertyRef("LaunchTime")
    launchtimeunix: PropertyRef = PropertyRef("LaunchTimeUnix")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    iaminstanceprofile: PropertyRef = PropertyRef("IamInstanceProfile")
    availabilityzone: PropertyRef = PropertyRef("AvailabilityZone")
    tenancy: PropertyRef = PropertyRef("Tenancy")
    hostresourcegrouparn: PropertyRef = PropertyRef("HostResourceGroupArn")
    platform: PropertyRef = PropertyRef("Platform")
    architecture: PropertyRef = PropertyRef("Architecture")
    virtualizationtype: PropertyRef = PropertyRef("VirtualizationType")
    hypervisor: PropertyRef = PropertyRef("Hypervisor")
    ebsoptimized: PropertyRef = PropertyRef("EbsOptimized")
    bootmode: PropertyRef = PropertyRef("BootMode")
    instancelifecycle: PropertyRef = PropertyRef("InstanceLifecycle")
    hibernationoptions: PropertyRef = PropertyRef("HibernationOption")
    consolelink: PropertyRef = PropertyRef("consolelink")
    arn: PropertyRef = PropertyRef("arn")
    userdata: PropertyRef = PropertyRef("UserData")


#    roleArn: PropertyRef = PropertyRef('RoleArn')


@dataclass(frozen=True)
class EC2InstanceToAwsAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EC2InstanceToAWSAccount(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: EC2InstanceToAwsAccountRelProperties = EC2InstanceToAwsAccountRelProperties()


@dataclass(frozen=True)
class EC2InstanceToEC2ReservationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EC2InstanceToEC2Reservation(CartographyRelSchema):
    target_node_label: str = "EC2Reservation"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"reservationid": PropertyRef("ReservationId")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF_EC2_RESERVATION"
    properties: EC2InstanceToEC2ReservationRelProperties = EC2InstanceToEC2ReservationRelProperties()


### TO DO  whenever  we are deploying to kubernetes we will uncomment this ###

# @dataclass(frozen=True)
# class EC2InstanceToIAMRoleRelProperties(CartographyRelProperties):
#     lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)

# @dataclass(frozen=True)
# class EC2InstanceToIAMRole(CartographyRelSchema):
#     target_node_label: str = 'AWSRole'
#     target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
#         {'arn': PropertyRef('RoleArn')},
#     )
#     direction: LinkDirection = LinkDirection.OUTWARD
#     rel_label: str = "USES"
#     properties: EC2InstanceToIAMRoleRelProperties = EC2InstanceToIAMRoleRelProperties()


@dataclass(frozen=True)
class EC2InstanceSchema(CartographyNodeSchema):
    label: str = "EC2Instance"
    properties: EC2InstanceNodeProperties = EC2InstanceNodeProperties()
    sub_resource_relationship: EC2InstanceToAWSAccount = EC2InstanceToAWSAccount()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            EC2InstanceToEC2Reservation(),
            # EC2InstanceToIAMRole(),
        ],
    )
