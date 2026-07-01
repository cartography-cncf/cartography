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
class ScalewayPublicGatewayProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", extra_index=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    type: PropertyRef = PropertyRef("type_")
    bandwidth: PropertyRef = PropertyRef("bandwidth")
    status: PropertyRef = PropertyRef("status")
    tags: PropertyRef = PropertyRef("tags")
    # Public egress IP of the NAT gateway (flattened from the ipv4 object).
    ipv4_address: PropertyRef = PropertyRef("ipv4_address", extra_index=True)
    # SSH bastion exposure signals.
    bastion_enabled: PropertyRef = PropertyRef("bastion_enabled")
    bastion_port: PropertyRef = PropertyRef("bastion_port")
    bastion_allowed_ips: PropertyRef = PropertyRef("bastion_allowed_ips")
    smtp_enabled: PropertyRef = PropertyRef("smtp_enabled")
    is_legacy: PropertyRef = PropertyRef("is_legacy")
    version: PropertyRef = PropertyRef("version")
    zone: PropertyRef = PropertyRef("zone")
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ScalewayPublicGatewayToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewayPublicGateway)
class ScalewayPublicGatewayToProjectRel(CartographyRelSchema):
    target_node_label: str = "ScalewayProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ScalewayPublicGatewayToProjectRelProperties = (
        ScalewayPublicGatewayToProjectRelProperties()
    )


@dataclass(frozen=True)
class ScalewayPublicGatewayToPrivateNetworkRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayPublicGateway)-[:ATTACHED_TO]->(:ScalewayPrivateNetwork)
# Represents the NAT / egress path: instances on the private network reach the
# internet through this gateway.
class ScalewayPublicGatewayToPrivateNetworkRel(CartographyRelSchema):
    target_node_label: str = "ScalewayPrivateNetwork"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("private_network_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ATTACHED_TO"
    properties: ScalewayPublicGatewayToPrivateNetworkRelProperties = (
        ScalewayPublicGatewayToPrivateNetworkRelProperties()
    )


@dataclass(frozen=True)
class ScalewayPublicGatewaySchema(CartographyNodeSchema):
    label: str = "ScalewayPublicGateway"
    properties: ScalewayPublicGatewayProperties = ScalewayPublicGatewayProperties()
    sub_resource_relationship: ScalewayPublicGatewayToProjectRel = (
        ScalewayPublicGatewayToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ScalewayPublicGatewayToPrivateNetworkRel(),
        ]
    )
