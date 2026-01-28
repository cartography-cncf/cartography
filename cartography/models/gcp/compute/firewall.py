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
class GCPFirewallNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    direction: PropertyRef = PropertyRef("direction")
    disabled: PropertyRef = PropertyRef("disabled")
    name: PropertyRef = PropertyRef("name", extra_index=True)
    priority: PropertyRef = PropertyRef("priority")
    self_link: PropertyRef = PropertyRef("selfLink")
    has_target_service_accounts: PropertyRef = PropertyRef(
        "has_target_service_accounts"
    )


@dataclass(frozen=True)
class GCPFirewallToVpcRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPFirewallToVpcRel(CartographyRelSchema):
    target_node_label: str = "GCPVpc"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("vpc_partial_uri"),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPFirewallToVpcRelProperties = GCPFirewallToVpcRelProperties()


@dataclass(frozen=True)
class GCPFirewallToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPFirewallToProjectRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("PROJECT_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPFirewallToProjectRelProperties = GCPFirewallToProjectRelProperties()


@dataclass(frozen=True)
class GCPFirewallSchema(CartographyNodeSchema):
    label: str = "GCPFirewall"
    properties: GCPFirewallNodeProperties = GCPFirewallNodeProperties()
    sub_resource_relationship: GCPFirewallToProjectRel = GCPFirewallToProjectRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GCPFirewallToVpcRel(),
        ]
    )
