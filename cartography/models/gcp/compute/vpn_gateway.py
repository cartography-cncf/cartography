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
class GCPVpnGatewayNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "partial_uri",
        extra_index=True,
        description="A partial resource URI representing this HA VPN Gateway. Has the form `projects/{project}/regions/{region}/vpnGateways/{gateway name}`.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    partial_uri: PropertyRef = PropertyRef("partial_uri", description="Same as `id`.")
    self_link: PropertyRef = PropertyRef(
        "self_link",
        description="The full resource URI representing this VPN Gateway. Has the form `https://www.googleapis.com/compute/v1/{partial_uri}`.",
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="The name of this VPN Gateway."
    )
    project_id: PropertyRef = PropertyRef(
        "project_id", description="The project ID that this VPN Gateway belongs to."
    )
    region: PropertyRef = PropertyRef(
        "region", description="The region of this VPN Gateway."
    )
    description: PropertyRef = PropertyRef(
        "description", description="A description for this VPN Gateway."
    )
    gateway_ip_version: PropertyRef = PropertyRef(
        "gateway_ip_version",
        description="The IP family of the gateway, e.g. IPV4 or IPV6.",
    )
    stack_type: PropertyRef = PropertyRef(
        "stack_type",
        description="The stack type of the gateway, e.g. IPV4_ONLY or IPV4_IPV6.",
    )
    network_partial_uri: PropertyRef = PropertyRef(
        "network_partial_uri",
        description="The partial URI of the VPC network this VPN Gateway is attached to, e.g. `projects/{project}/global/networks/{network name}`.",
    )
    creation_timestamp: PropertyRef = PropertyRef(
        "creation_timestamp",
        description="The creation timestamp of this VPN Gateway.",
    )


@dataclass(frozen=True)
class GCPVpnGatewayToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPVpnGatewayToProjectRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("PROJECT_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPVpnGatewayToProjectRelProperties = (
        GCPVpnGatewayToProjectRelProperties()
    )


@dataclass(frozen=True)
class GCPVpnGatewayToVpcRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPVpnGatewayToVpcRel(CartographyRelSchema):
    """Points from the VPN gateway to the VPC network it is attached to."""

    target_node_label: str = "GCPVpc"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("network_partial_uri"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "PART_OF_VPC"
    properties: GCPVpnGatewayToVpcRelProperties = GCPVpnGatewayToVpcRelProperties()


@dataclass(frozen=True)
class GCPVpnGatewaySchema(CartographyNodeSchema):
    """Representation of a GCP [HA VPN Gateway](https://cloud.google.com/compute/docs/reference/rest/v1/vpnGateways)."""

    label: str = "GCPVpnGateway"
    properties: GCPVpnGatewayNodeProperties = GCPVpnGatewayNodeProperties()
    sub_resource_relationship: GCPVpnGatewayToProjectRel = GCPVpnGatewayToProjectRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GCPVpnGatewayToVpcRel(),
        ]
    )
