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

# AWSELBV2TargetGroup Schema


@dataclass(frozen=True)
class ELBV2TargetGroupNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "TargetGroupArn",
        description="Unique identifier for this `AWSELBV2TargetGroup` node.",
    )
    arn: PropertyRef = PropertyRef(
        "TargetGroupArn",
        extra_index=True,
        description="Amazon Resource Name (ARN) of this `AWSELBV2TargetGroup` node.",
    )
    name: PropertyRef = PropertyRef(
        "TargetGroupName", description="Name of this `AWSELBV2TargetGroup` node."
    )
    target_type: PropertyRef = PropertyRef(
        "TargetType",
        description="Type of resource registered as a target in the target group.",
    )
    protocol: PropertyRef = PropertyRef(
        "Protocol",
        description="Protocol used by the listener or target group.",
    )
    port: PropertyRef = PropertyRef(
        "Port",
        description="Port on which the listener or target group receives traffic.",
    )
    vpc_id: PropertyRef = PropertyRef(
        "VpcId",
        description="Identifier of the VPC linked to this `AWSELBV2TargetGroup` node.",
    )
    region: PropertyRef = PropertyRef(
        "Region",
        set_in_kwargs=True,
        description="AWS Region containing this `AWSELBV2TargetGroup` node.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that updated this `AWSELBV2TargetGroup` node.",
    )


@dataclass(frozen=True)
class ELBV2TargetGroupToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ELBV2TargetGroupToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSELBV2TargetGroup`."

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ELBV2TargetGroupToAWSAccountRelProperties = (
        ELBV2TargetGroupToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class ELBV2TargetGroupToLoadBalancerV2RelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ELBV2TargetGroupToLoadBalancerV2Rel(CartographyRelSchema):
    "Represents a `ELBV2_TARGET_GROUP` relationship from `AWSLoadBalancerV2` to `AWSELBV2TargetGroup`."

    target_node_label: str = "AWSLoadBalancerV2"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("LoadBalancerId", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "ELBV2_TARGET_GROUP"
    properties: ELBV2TargetGroupToLoadBalancerV2RelProperties = (
        ELBV2TargetGroupToLoadBalancerV2RelProperties()
    )


@dataclass(frozen=True)
class ELBV2TargetGroupSchema(CartographyNodeSchema):
    "Represents an `AWSELBV2TargetGroup` node in the AWS graph."

    label: str = "AWSELBV2TargetGroup"
    # DEPRECATED: legacy ELBV2TargetGroup node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["ELBV2TargetGroup"])
    properties: ELBV2TargetGroupNodeProperties = ELBV2TargetGroupNodeProperties()
    sub_resource_relationship: ELBV2TargetGroupToAWSAccountRel = (
        ELBV2TargetGroupToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [ELBV2TargetGroupToLoadBalancerV2Rel()],
    )


# AWSELBV2TargetGroup -> AWSECSService MatchLink


@dataclass(frozen=True)
class ELBV2TargetGroupToECSServiceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label",
        set_in_kwargs=True,
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)
    container_name: PropertyRef = PropertyRef(
        "ContainerName",
        description="Name of the container reached through this relationship.",
    )
    container_port: PropertyRef = PropertyRef(
        "ContainerPort", description="Container port reached through this relationship."
    )


@dataclass(frozen=True)
class ELBV2TargetGroupToECSServiceMatchLink(CartographyRelSchema):
    """(:AWSELBV2TargetGroup)-[:TARGETS]->(:AWSECSService)"""

    target_node_label: str = "AWSECSService"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ServiceArn")},
    )
    source_node_label: str = "AWSELBV2TargetGroup"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("TargetGroupArn")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "TARGETS"
    properties: ELBV2TargetGroupToECSServiceRelProperties = (
        ELBV2TargetGroupToECSServiceRelProperties()
    )


# LoadBalancerV2 Schema


@dataclass(frozen=True)
class LoadBalancerV2NodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "DNSName", description="Currently set to the `dnsname` of the load balancer."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )
    region: PropertyRef = PropertyRef(
        "Region", set_in_kwargs=True, description="The region of the load balancer"
    )
    name: PropertyRef = PropertyRef(
        "LoadBalancerName", description="The name of the load balancer"
    )
    dnsname: PropertyRef = PropertyRef(
        "DNSName", extra_index=True, description="The DNS name of the load balancer."
    )
    canonicalhostedzonenameid: PropertyRef = PropertyRef(
        "CanonicalHostedZoneId",
        description="The ID of the Amazon Route 53 hosted zone for the load balancer.",
    )
    type: PropertyRef = PropertyRef(
        "Type", description="Can be `application` or `network`"
    )
    scheme: PropertyRef = PropertyRef(
        "Scheme",
        description="The type of load balancer.  If scheme is `internet-facing`, the load balancer has a public DNS name that resolves to a public IP address.  If scheme is `internal`, the load balancer has a public DNS name that resolves to a private IP address.",
    )
    exposed_internet: PropertyRef = PropertyRef(
        "exposed_internet",
        extra_index=True,
        description="The `exposed_internet` flag is set to `True` by the `aws_ec2_asset_exposure` analysis job when internet reachability is inferred. For NLBs (`type='network'`), this is based on `scheme='internet-facing'` and listener presence. For ALBs, this requires `scheme='internet-facing'` plus a security group path open from `0.0.0.0/0` to a listener port.",
    )  # Populated by AWS_EC2_ASSET_EXPOSURE_JOBS.
    arn: PropertyRef = PropertyRef(
        "LoadBalancerArn",
        extra_index=True,
        description="The Amazon Resource Name (ARN) of the load balancer.",
    )
    createdtime: PropertyRef = PropertyRef(
        "CreatedTime", description="The date and time the load balancer was created."
    )


@dataclass(frozen=True)
class LoadBalancerV2ToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class LoadBalancerV2ToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSLoadBalancerV2`."

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: LoadBalancerV2ToAWSAccountRelProperties = (
        LoadBalancerV2ToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class LoadBalancerV2ToEC2SecurityGroupRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class LoadBalancerV2ToEC2SecurityGroupRel(CartographyRelSchema):
    "Represents a `MEMBER_OF_EC2_SECURITY_GROUP` relationship from `AWSLoadBalancerV2` to `AWSEC2SecurityGroup`."

    target_node_label: str = "AWSEC2SecurityGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"groupid": PropertyRef("SecurityGroupIds", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF_EC2_SECURITY_GROUP"
    properties: LoadBalancerV2ToEC2SecurityGroupRelProperties = (
        LoadBalancerV2ToEC2SecurityGroupRelProperties()
    )


@dataclass(frozen=True)
class LoadBalancerV2ToEC2SubnetRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class LoadBalancerV2ToEC2SubnetRel(CartographyRelSchema):
    "Represents a `SUBNET` relationship from `AWSLoadBalancerV2` to `AWSEC2Subnet`."

    target_node_label: str = "AWSEC2Subnet"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"subnetid": PropertyRef("SubnetIds", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "SUBNET"
    properties: LoadBalancerV2ToEC2SubnetRelProperties = (
        LoadBalancerV2ToEC2SubnetRelProperties()
    )


@dataclass(frozen=True)
class LoadBalancerV2Schema(CartographyNodeSchema):
    """
    LoadBalancerV2 schema (Application and Network Load Balancers).

    Target relationships (EXPOSE) are defined as MatchLinks below for introspection.
    """

    label: str = "AWSLoadBalancerV2"
    properties: LoadBalancerV2NodeProperties = LoadBalancerV2NodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [
            "LoadBalancer",  # Ontology node label
            # DEPRECATED: legacy LoadBalancerV2 node label will be removed in v1.0.0.
            "LoadBalancerV2",
        ]
    )
    sub_resource_relationship: LoadBalancerV2ToAWSAccountRel = (
        LoadBalancerV2ToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            LoadBalancerV2ToEC2SecurityGroupRel(),
            LoadBalancerV2ToEC2SubnetRel(),
        ],
    )


# LoadBalancerV2 Target MatchLinks
# These define EXPOSE relationships to various target types


@dataclass(frozen=True)
class LoadBalancerV2ToTargetRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label",
        set_in_kwargs=True,
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)
    port: PropertyRef = PropertyRef(
        "Port",
        description="Port on which the listener or target group receives traffic.",
    )
    protocol: PropertyRef = PropertyRef(
        "Protocol", description="Protocol used by the listener or target group."
    )
    target_group_arn: PropertyRef = PropertyRef(
        "TargetGroupArn",
        description="ARN of the Elastic Load Balancing target group represented by this relationship.",
    )


@dataclass(frozen=True)
class LoadBalancerV2ToEC2InstanceMatchLink(CartographyRelSchema):
    """(:LoadBalancerV2)-[:EXPOSE]->(:AWSEC2Instance)"""

    target_node_label: str = "AWSEC2Instance"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"instanceid": PropertyRef("TargetId")},
    )
    source_node_label: str = "AWSLoadBalancerV2"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("LoadBalancerId")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "EXPOSE"
    properties: LoadBalancerV2ToTargetRelProperties = (
        LoadBalancerV2ToTargetRelProperties()
    )


@dataclass(frozen=True)
class LoadBalancerV2ToEC2PrivateIpMatchLink(CartographyRelSchema):
    """(:LoadBalancerV2)-[:EXPOSE]->(:AWSEC2PrivateIp)"""

    target_node_label: str = "AWSEC2PrivateIp"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"private_ip_address": PropertyRef("TargetId")},
    )
    source_node_label: str = "AWSLoadBalancerV2"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("LoadBalancerId")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "EXPOSE"
    properties: LoadBalancerV2ToTargetRelProperties = (
        LoadBalancerV2ToTargetRelProperties()
    )


@dataclass(frozen=True)
class LoadBalancerV2ToAWSLambdaMatchLink(CartographyRelSchema):
    """(:LoadBalancerV2)-[:EXPOSE]->(:AWSLambda)"""

    target_node_label: str = "AWSLambda"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TargetId")},
    )
    source_node_label: str = "AWSLoadBalancerV2"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("LoadBalancerId")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "EXPOSE"
    properties: LoadBalancerV2ToTargetRelProperties = (
        LoadBalancerV2ToTargetRelProperties()
    )


@dataclass(frozen=True)
class LoadBalancerV2ToLoadBalancerV2MatchLink(CartographyRelSchema):
    """(:LoadBalancerV2)-[:EXPOSE]->(:LoadBalancerV2) for ALB targets"""

    target_node_label: str = "AWSLoadBalancerV2"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("TargetId")},
    )
    source_node_label: str = "AWSLoadBalancerV2"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("LoadBalancerId")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "EXPOSE"
    properties: LoadBalancerV2ToTargetRelProperties = (
        LoadBalancerV2ToTargetRelProperties()
    )


# AWSELBV2Listener Schema


@dataclass(frozen=True)
class ELBV2ListenerNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "ListenerArn", description="Unique identifier for this `AWSELBV2Listener` node."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that updated this `AWSELBV2Listener` node.",
    )
    port: PropertyRef = PropertyRef(
        "Port",
        description="Port on which the listener or target group receives traffic.",
    )
    protocol: PropertyRef = PropertyRef(
        "Protocol", description="Protocol used by the listener or target group."
    )
    ssl_policy: PropertyRef = PropertyRef(
        "SslPolicy",
        description="TLS security policy configured on the listener.",
    )
    targetgrouparn: PropertyRef = PropertyRef(
        "TargetGroupArn",
        description="ARN of the targetgrouparn linked to this `AWSELBV2Listener` node.",
    )
    mutual_authentication_mode: PropertyRef = PropertyRef(
        "MutualAuthenticationMode",
        description="Mutual TLS authentication mode configured on the listener.",
    )
    trust_store_arn: PropertyRef = PropertyRef(
        "TrustStoreArn",
        description="ARN of the trust store linked to this `AWSELBV2Listener` node.",
    )
    ignore_client_certificate_expiry: PropertyRef = PropertyRef(
        "IgnoreClientCertificateExpiry",
        description="Whether this `AWSELBV2Listener` node ignores client certificate expiry.",
    )
    trust_store_association_status: PropertyRef = PropertyRef(
        "TrustStoreAssociationStatus",
        description="Current status of the listener trust-store association.",
    )
    advertise_trust_store_ca_names: PropertyRef = PropertyRef(
        "AdvertiseTrustStoreCaNames",
        description="Whether the listener advertises certificate-authority names from its trust store.",
    )


@dataclass(frozen=True)
class ELBV2ListenerToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ELBV2ListenerToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSELBV2Listener`."

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ELBV2ListenerToAWSAccountRelProperties = (
        ELBV2ListenerToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class ELBV2ListenerToLoadBalancerV2RelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ELBV2ListenerToLoadBalancerV2Rel(CartographyRelSchema):
    "Represents a `ELBV2_LISTENER` relationship from `AWSLoadBalancerV2` to `AWSELBV2Listener`."

    target_node_label: str = "AWSLoadBalancerV2"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("LoadBalancerId")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "ELBV2_LISTENER"
    properties: ELBV2ListenerToLoadBalancerV2RelProperties = (
        ELBV2ListenerToLoadBalancerV2RelProperties()
    )


@dataclass(frozen=True)
class ELBV2ListenerSchema(CartographyNodeSchema):
    """
    AWSELBV2Listener schema for load balancer listeners.
    """

    label: str = "AWSELBV2Listener"
    # DEPRECATED: legacy ELBV2Listener node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["ELBV2Listener", "Endpoint"])
    properties: ELBV2ListenerNodeProperties = ELBV2ListenerNodeProperties()
    sub_resource_relationship: ELBV2ListenerToAWSAccountRel = (
        ELBV2ListenerToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [ELBV2ListenerToLoadBalancerV2Rel()],
    )
