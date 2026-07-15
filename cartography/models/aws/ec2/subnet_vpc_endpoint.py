from dataclasses import dataclass

from cartography.models.aws.ec2.subnet_instance import EC2SubnetToAWSAccountRel
from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class EC2SubnetVPCEndpointNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("SubnetId", description="same as subnetid")
    subnetid: PropertyRef = PropertyRef(
        "SubnetId", extra_index=True, description="The ID of the subnet"
    )
    subnet_id: PropertyRef = PropertyRef(
        "SubnetId", extra_index=True, description="The ID of the subnet"
    )
    region: PropertyRef = PropertyRef(
        "Region",
        set_in_kwargs=True,
        description="The AWS region the subnet is installed on",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )


@dataclass(frozen=True)
class EC2SubnetToVPCEndpointRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EC2SubnetToVPCEndpointRel(CartographyRelSchema):
    "Represents a `USES_SUBNET` relationship from `AWSVpcEndpoint` to `AWSEC2Subnet`."

    target_node_label: str = "AWSVpcEndpoint"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("VpcEndpointId")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "USES_SUBNET"
    properties: EC2SubnetToVPCEndpointRelProperties = (
        EC2SubnetToVPCEndpointRelProperties()
    )


@dataclass(frozen=True)
class EC2SubnetVPCEndpointSchema(CartographyNodeSchema):
    "Represents a subnet in an Amazon EC2 virtual private cloud."

    # Implementation note:
    # EC2 Subnet as known by describe-vpc-endpoints.
    # Creates stub subnet nodes and USES_SUBNET relationships from VPC endpoints.

    label: str = "AWSEC2Subnet"
    properties: EC2SubnetVPCEndpointNodeProperties = (
        EC2SubnetVPCEndpointNodeProperties()
    )
    # DEPRECATED: legacy EC2Subnet node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["EC2Subnet", "Subnet"])
    sub_resource_relationship: EC2SubnetToAWSAccountRel = EC2SubnetToAWSAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            EC2SubnetToVPCEndpointRel(),
        ],
    )
