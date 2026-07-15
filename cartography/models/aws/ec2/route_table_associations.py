from dataclasses import dataclass

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
class RouteTableAssociationNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="The ID of the route table association"
    )
    route_table_association_id: PropertyRef = PropertyRef(
        "id",
        extra_index=True,
        description="The ID of the route table association (same as id)",
    )
    target: PropertyRef = PropertyRef(
        "_target",
        description="Subnet or gateway identifier associated with the route table.",
    )
    gateway_id: PropertyRef = PropertyRef(
        "gateway_id", description="The ID of the gateway (if associated with a gateway)"
    )
    main: PropertyRef = PropertyRef(
        "main", description="Whether this is the main route table association"
    )
    route_table_id: PropertyRef = PropertyRef(
        "route_table_id", description="The ID of the route table"
    )
    subnet_id: PropertyRef = PropertyRef(
        "subnet_id", description="The ID of the subnet (if associated with a subnet)"
    )
    association_state: PropertyRef = PropertyRef(
        "association_state", description="The state of the association"
    )
    association_state_message: PropertyRef = PropertyRef(
        "association_state_message",
        description="The message describing the state of the association",
    )
    region: PropertyRef = PropertyRef(
        "Region", set_in_kwargs=True, description="The AWS region the association is in"
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )


@dataclass(frozen=True)
class RouteTableAssociationToAWSAccountRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class RouteTableAssociationToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSEC2RouteTableAssociation`."

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: RouteTableAssociationToAWSAccountRelRelProperties = (
        RouteTableAssociationToAWSAccountRelRelProperties()
    )


@dataclass(frozen=True)
class RouteTableAssociationToSubnetRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class RouteTableAssociationToSubnetRel(CartographyRelSchema):
    "Represents a `ASSOCIATED_SUBNET` relationship from `AWSEC2RouteTableAssociation` to `AWSEC2Subnet`."

    target_node_label: str = "AWSEC2Subnet"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"subnetid": PropertyRef("subnet_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ASSOCIATED_SUBNET"
    properties: RouteTableAssociationToSubnetRelRelProperties = (
        RouteTableAssociationToSubnetRelRelProperties()
    )


@dataclass(frozen=True)
class RouteTableAssociationToIgwRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class RouteTableAssociationToIgwRel(CartographyRelSchema):
    "Represents a `ASSOCIATED_IGW_FOR_INGRESS` relationship from `AWSEC2RouteTableAssociation` to `AWSInternetGateway`."

    target_node_label: str = "AWSInternetGateway"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("gateway_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ASSOCIATED_IGW_FOR_INGRESS"
    properties: RouteTableAssociationToIgwRelRelProperties = (
        RouteTableAssociationToIgwRelRelProperties()
    )


@dataclass(frozen=True)
class RouteTableAssociationSchema(CartographyNodeSchema):
    "Represents an `AWSEC2RouteTableAssociation` node in the AWS graph."

    label: str = "AWSEC2RouteTableAssociation"
    # DEPRECATED: legacy EC2RouteTableAssociation node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["EC2RouteTableAssociation"])
    properties: RouteTableAssociationNodeProperties = (
        RouteTableAssociationNodeProperties()
    )
    sub_resource_relationship: RouteTableAssociationToAWSAccountRel = (
        RouteTableAssociationToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            RouteTableAssociationToSubnetRel(),
            RouteTableAssociationToIgwRel(),
        ],
    )
