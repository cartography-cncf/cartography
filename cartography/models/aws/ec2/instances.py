from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_source_node_matcher
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import SourceNodeMatcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class EC2InstanceNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "InstanceId", description="Same as `instanceid` below."
    )
    arn: PropertyRef = PropertyRef(
        "Arn",
        extra_index=True,
        description="The Amazon Resource Name of the instance, e.g. `arn:aws:ec2:{region}:{account}:instance/{instanceid}`. Synthesized by cartography for IAM permission matching.",
    )
    instanceid: PropertyRef = PropertyRef(
        "InstanceId",
        extra_index=True,
        description="The instance id provided by AWS.  This is [globally unique](https://forums.aws.amazon.com/thread.jspa?threadID=137203)",
    )
    publicdnsname: PropertyRef = PropertyRef(
        "PublicDnsName",
        extra_index=True,
        description="The public DNS name assigned to the instance",
    )
    privateipaddress: PropertyRef = PropertyRef(
        "PrivateIpAddress",
        description="The private IPv4 address assigned to the instance",
    )
    publicipaddress: PropertyRef = PropertyRef(
        "PublicIpAddress",
        description="The public IPv4 address assigned to the instance if applicable",
    )
    imageid: PropertyRef = PropertyRef(
        "ImageId",
        description="The ID of the [Amazon Machine Image](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/AMIs.html) used to launch the instance",
    )
    instancetype: PropertyRef = PropertyRef(
        "InstanceType",
        description="The instance type.  See API docs linked above for specifics.",
    )
    monitoringstate: PropertyRef = PropertyRef(
        "MonitoringState",
        description="Whether monitoring is enabled.  Valid Values: disabled, disabling, enabled,  pending.",
    )
    state: PropertyRef = PropertyRef(
        "State",
        description="The [current state](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_InstanceState.html) of the instance.",
    )
    launchtime: PropertyRef = PropertyRef(
        "LaunchTime", description="The time the instance was launched"
    )
    launchtimeunix: PropertyRef = PropertyRef(
        "LaunchTimeUnix",
        description="EC2 instance launch time expressed as a Unix timestamp.",
    )
    region: PropertyRef = PropertyRef(
        "Region",
        set_in_kwargs=True,
        description="The AWS region this Instance is running in",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )
    iaminstanceprofile: PropertyRef = PropertyRef(
        "IamInstanceProfile",
        description="The IAM instance profile associated with the instance, if applicable.",
    )
    availabilityzone: PropertyRef = PropertyRef(
        "AvailabilityZone", description="The Availability Zone of the instance."
    )
    tenancy: PropertyRef = PropertyRef(
        "Tenancy", description="The tenancy of the instance."
    )
    hostresourcegrouparn: PropertyRef = PropertyRef(
        "HostResourceGroupArn",
        description="The ARN of the host resource group in which to launch the instances.",
    )
    platform: PropertyRef = PropertyRef(
        "Platform",
        description="The value is `Windows` for Windows instances; otherwise blank.",
    )
    architecture: PropertyRef = PropertyRef(
        "Architecture", description="The architecture of the image."
    )
    ebsoptimized: PropertyRef = PropertyRef(
        "EbsOptimized",
        description="Indicates whether the instance is optimized for Amazon EBS I/O.",
    )
    bootmode: PropertyRef = PropertyRef(
        "BootMode", description="The boot mode of the instance."
    )
    instancelifecycle: PropertyRef = PropertyRef(
        "InstanceLifecycle",
        description="Indicates whether this is a Spot Instance or a Scheduled Instance.",
    )
    hibernationoptions: PropertyRef = PropertyRef(
        "HibernationOption",
        description="Indicates whether the instance is enabled for hibernation.",
    )
    metadatahttptokens: PropertyRef = PropertyRef(
        "MetadataHttpTokens",
        extra_index=True,
        description="The EC2 metadata service token setting. `required` means IMDSv2 is required and IMDSv1 is disabled; `optional` means either IMDSv1 or IMDSv2 may be used.",
    )
    metadatahttpputresponsehoplimit: PropertyRef = PropertyRef(
        "MetadataHttpPutResponseHopLimit",
        description="The maximum number of network hops that an IMDSv2 session token response can travel.",
    )
    metadatahttpendpoint: PropertyRef = PropertyRef(
        "MetadataHttpEndpoint",
        description="Indicates whether the instance metadata HTTP endpoint is enabled.",
    )
    metadatahttpprotocolipv6: PropertyRef = PropertyRef(
        "MetadataHttpProtocolIpv6",
        description="Indicates whether the IPv6 endpoint for the instance metadata service is enabled.",
    )
    metadatainstancetags: PropertyRef = PropertyRef(
        "MetadataInstanceTags",
        description="Indicates whether instance tags are exposed through the instance metadata service.",
    )
    imdsaccessmode: PropertyRef = PropertyRef(
        "ImdsAccessMode",
        description="A derived helper field that normalizes the `metadatahttptokens` setting to `v2_only` or `v1_or_v2` for easier security queries.",
    )
    imdsv1enabled: PropertyRef = PropertyRef(
        "ImdsV1Enabled",
        description="A derived boolean that is `true` when IMDSv1 remains allowed on the instance.",
    )
    imdsv2required: PropertyRef = PropertyRef(
        "ImdsV2Required",
        description="A derived boolean that is `true` when the instance requires IMDSv2 and disables IMDSv1.",
    )
    exposed_internet: PropertyRef = PropertyRef(
        "exposed_internet",
        extra_index=True,
        description="The `exposed_internet` flag on an EC2 instance is set to `True` when (1) the instance is part of an EC2 security group or is connected to a network interface connected to an EC2 security group that allows connectivity from the 0.0.0.0/0 subnet or (2) the instance is connected to an Elastic Load Balancer that has its own `exposed_internet` flag set to `True`.",
    )  # Populated by AWS_EC2_ASSET_EXPOSURE_JOBS.
    eks_cluster_name: PropertyRef = PropertyRef(
        "EksClusterName",
        description="The name of the EKS cluster this instance belongs to, if applicable. Extracted from instance tags.",
    )
    ipv6address: PropertyRef = PropertyRef(
        "IPv6Address",
        description="The primary IPv6 address assigned to the instance's primary network interface (DeviceIndex=0), if any.",
    )


@dataclass(frozen=True)
class EC2InstanceToAWSAccountRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EC2InstanceToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSEC2Instance`."

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: EC2InstanceToAWSAccountRelRelProperties = (
        EC2InstanceToAWSAccountRelRelProperties()
    )


@dataclass(frozen=True)
class EC2InstanceToEC2ReservationRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EC2InstanceToEC2ReservationRel(CartographyRelSchema):
    "Represents a `MEMBER_OF_EC2_RESERVATION` relationship from `AWSEC2Instance` to `AWSEC2Reservation`."

    target_node_label: str = "AWSEC2Reservation"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"reservationid": PropertyRef("ReservationId")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF_EC2_RESERVATION"
    properties: EC2InstanceToEC2ReservationRelRelProperties = (
        EC2InstanceToEC2ReservationRelRelProperties()
    )


@dataclass(frozen=True)
class EC2InstanceToInstanceProfileRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EC2InstanceToInstanceProfileRel(CartographyRelSchema):
    "Represents a `INSTANCE_PROFILE` relationship from `AWSEC2Instance` to `AWSInstanceProfile`."

    target_node_label: str = "AWSInstanceProfile"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("IamInstanceProfile")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "INSTANCE_PROFILE"
    properties: EC2InstanceToInstanceProfileRelRelProperties = (
        EC2InstanceToInstanceProfileRelRelProperties()
    )


@dataclass(frozen=True)
class EC2InstanceToEKSClusterRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EC2InstanceToEKSClusterRel(CartographyRelSchema):
    "Represents a `MEMBER_OF_EKS_CLUSTER` relationship from `AWSEC2Instance` to `AWSEKSCluster`."

    target_node_label: str = "AWSEKSCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "name": PropertyRef("EksClusterName"),
        },
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF_EKS_CLUSTER"
    properties: EC2InstanceToEKSClusterRelRelProperties = (
        EC2InstanceToEKSClusterRelRelProperties()
    )


@dataclass(frozen=True)
class EC2InstanceSchema(CartographyNodeSchema):
    "Represents an `AWSEC2Instance` node in the AWS graph."

    label: str = "AWSEC2Instance"
    # DEPRECATED: legacy EC2Instance node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        ["EC2Instance", "ComputeInstance"]
    )
    properties: EC2InstanceNodeProperties = EC2InstanceNodeProperties()
    sub_resource_relationship: EC2InstanceToAWSAccountRel = EC2InstanceToAWSAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            EC2InstanceToEC2ReservationRel(),
            EC2InstanceToInstanceProfileRel(),
            EC2InstanceToEKSClusterRel(),
        ],
    )


@dataclass(frozen=True)
class EC2InstanceToRoleAssumesRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)


@dataclass(frozen=True)
# Canonical ontology edge: (:AWSEC2Instance)-[:ASSUMES]->(:AWSRole).
# The instance runs with the permissions of the role attached through its
# instance profile: AWSEC2Instance-[:INSTANCE_PROFILE]->AWSInstanceProfile
# -[:ASSOCIATED_WITH]->AWSRole. There is no direct instance->role edge in the
# AWS API, so the pairs are assembled from that binding chain and loaded as a
# MatchLink.
class EC2InstanceToRoleAssumesMatchLink(CartographyRelSchema):
    "Represents a `ASSUMES` relationship from `AWSEC2Instance` to `AWSRole`."

    rel_label: str = "ASSUMES"
    direction: LinkDirection = LinkDirection.OUTWARD
    properties: EC2InstanceToRoleAssumesRelProperties = (
        EC2InstanceToRoleAssumesRelProperties()
    )
    target_node_label: str = "AWSRole"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("role_arn")},
    )
    source_node_label: str = "AWSEC2Instance"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("instance_id")},
    )
