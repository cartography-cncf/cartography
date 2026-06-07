from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class VercelFirewallConfigNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    enabled: PropertyRef = PropertyRef("firewallEnabled")
    updated_at: PropertyRef = PropertyRef("updatedAt")


@dataclass(frozen=True)
class VercelFirewallConfigToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:VercelProject)-[:RESOURCE]->(:VercelFirewallConfig)
class VercelFirewallConfigToProjectRel(CartographyRelSchema):
    target_node_label: str = "VercelProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("project_id", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: VercelFirewallConfigToProjectRelProperties = (
        VercelFirewallConfigToProjectRelProperties()
    )


@dataclass(frozen=True)
class VercelFirewallConfigSchema(CartographyNodeSchema):
    label: str = "VercelFirewallConfig"
    properties: VercelFirewallConfigNodeProperties = (
        VercelFirewallConfigNodeProperties()
    )
    sub_resource_relationship: VercelFirewallConfigToProjectRel = (
        VercelFirewallConfigToProjectRel()
    )
