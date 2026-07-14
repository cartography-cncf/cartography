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
    id: PropertyRef = PropertyRef("id", description="Firewall configuration ID.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Timestamp of the last update."
    )
    enabled: PropertyRef = PropertyRef(
        "firewallEnabled", description="Whether the firewall is enabled."
    )
    updated_at: PropertyRef = PropertyRef(
        "updatedAt",
        description="Timestamp when the firewall configuration was last updated.",
    )


@dataclass(frozen=True)
class VercelFirewallConfigToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:VercelProject)-[:RESOURCE]->(:VercelFirewallConfig)
class VercelFirewallConfigToProjectRel(CartographyRelSchema):
    """The Vercel project contains this firewall configuration as a resource."""

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
    """The Vercel firewall configuration for a project."""

    label: str = "VercelFirewallConfig"
    properties: VercelFirewallConfigNodeProperties = (
        VercelFirewallConfigNodeProperties()
    )
    sub_resource_relationship: VercelFirewallConfigToProjectRel = (
        VercelFirewallConfigToProjectRel()
    )
