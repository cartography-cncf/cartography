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
class ScalewayPublicGatewayPatRuleProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", extra_index=True)
    # Inbound forwarding: public_port on the gateway IP -> private_ip:private_port.
    public_port: PropertyRef = PropertyRef("public_port")
    private_ip: PropertyRef = PropertyRef("private_ip", extra_index=True)
    private_port: PropertyRef = PropertyRef("private_port")
    protocol: PropertyRef = PropertyRef("protocol")
    zone: PropertyRef = PropertyRef("zone")
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ScalewayPublicGatewayPatRuleToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewayPublicGatewayPatRule)
class ScalewayPublicGatewayPatRuleToProjectRel(CartographyRelSchema):
    target_node_label: str = "ScalewayProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ScalewayPublicGatewayPatRuleToProjectRelProperties = (
        ScalewayPublicGatewayPatRuleToProjectRelProperties()
    )


@dataclass(frozen=True)
class ScalewayPublicGatewayPatRuleToGatewayRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayPublicGateway)-[:HAS]->(:ScalewayPublicGatewayPatRule)
class ScalewayPublicGatewayPatRuleToGatewayRel(CartographyRelSchema):
    target_node_label: str = "ScalewayPublicGateway"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("gateway_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS"
    properties: ScalewayPublicGatewayPatRuleToGatewayRelProperties = (
        ScalewayPublicGatewayPatRuleToGatewayRelProperties()
    )


@dataclass(frozen=True)
class ScalewayPublicGatewayPatRuleSchema(CartographyNodeSchema):
    label: str = "ScalewayPublicGatewayPatRule"
    properties: ScalewayPublicGatewayPatRuleProperties = (
        ScalewayPublicGatewayPatRuleProperties()
    )
    sub_resource_relationship: ScalewayPublicGatewayPatRuleToProjectRel = (
        ScalewayPublicGatewayPatRuleToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ScalewayPublicGatewayPatRuleToGatewayRel(),
        ]
    )
