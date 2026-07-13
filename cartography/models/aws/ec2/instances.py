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
    id: PropertyRef = PropertyRef("InstanceId")
    arn: PropertyRef = PropertyRef("Arn", extra_index=True)
    instanceid: PropertyRef = PropertyRef("InstanceId", extra_index=True)
    publicdnsname: PropertyRef = PropertyRef("PublicDnsName", extra_index=True)
    privateipaddress: PropertyRef = PropertyRef("PrivateIpAddress")
    publicipaddress: PropertyRef = PropertyRef("PublicIpAddress")
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
    ebsoptimized: PropertyRef = PropertyRef("EbsOptimized")
    bootmode: PropertyRef = PropertyRef("BootMode")
    instancelifecycle: PropertyRef = PropertyRef("InstanceLifecycle")
    hibernationoptions: PropertyRef = PropertyRef("HibernationOption")
    metadatahttptokens: PropertyRef = PropertyRef(
        "MetadataHttpTokens", extra_index=True
    )
    metadatahttpputresponsehoplimit: PropertyRef = PropertyRef(
        "MetadataHttpPutResponseHopLimit"
    )
    metadatahttpendpoint: PropertyRef = PropertyRef("MetadataHttpEndpoint")
    metadatahttpprotocolipv6: PropertyRef = PropertyRef("MetadataHttpProtocolIpv6")
    metadatainstancetags: PropertyRef = PropertyRef("MetadataInstanceTags")
    imdsaccessmode: PropertyRef = PropertyRef("ImdsAccessMode")
    imdsv1enabled: PropertyRef = PropertyRef("ImdsV1Enabled")
    imdsv2required: PropertyRef = PropertyRef("ImdsV2Required")
    exposed_internet: PropertyRef = PropertyRef(
        "exposed_internet", extra_index=True
    )  # Populated by AWS_EC2_ASSET_EXPOSURE_JOBS.
    eks_cluster_name: PropertyRef = PropertyRef("EksClusterName")
    ipv6address: PropertyRef = PropertyRef("IPv6Address")


@dataclass(frozen=True)
class EC2InstanceToAWSAccountRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EC2InstanceToAWSAccountRel(CartographyRelSchema):
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
    target_node_label: str = "EC2Reservation"
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
    target_node_label: str = "EKSCluster"
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
    label: str = "EC2Instance"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["ComputeInstance"])
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
# Canonical ontology edge: (:EC2Instance)-[:ASSUMES]->(:AWSRole).
# The instance runs with the permissions of the role attached through its
# instance profile: EC2Instance-[:INSTANCE_PROFILE]->AWSInstanceProfile
# -[:ASSOCIATED_WITH]->AWSRole. There is no direct instance->role edge in the
# AWS API, so the pairs are assembled from that binding chain and loaded as a
# MatchLink.
class EC2InstanceToRoleAssumesMatchLink(CartographyRelSchema):
    rel_label: str = "ASSUMES"
    direction: LinkDirection = LinkDirection.OUTWARD
    properties: EC2InstanceToRoleAssumesRelProperties = (
        EC2InstanceToRoleAssumesRelProperties()
    )
    target_node_label: str = "AWSRole"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("role_arn")},
    )
    source_node_label: str = "EC2Instance"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("instance_id")},
    )
