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
class VercelFirewallBypassRuleNodeProperties(CartographyNodeProperties):
    # Note: Vercel's firewall bypass endpoint returns PascalCase field names.
    id: PropertyRef = PropertyRef("Id", description="Firewall bypass rule ID.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Timestamp of the last update."
    )
    domain: PropertyRef = PropertyRef(
        "Domain", description="Domain to which the bypass rule applies."
    )
    ip: PropertyRef = PropertyRef(
        "Ip", description="IP address allowed by the bypass rule."
    )
    note: PropertyRef = PropertyRef(
        "Note", description="Operator-provided note for the bypass rule."
    )
    action: PropertyRef = PropertyRef(
        "Action", description="Action performed by the bypass rule."
    )
    created_at: PropertyRef = PropertyRef(
        "CreatedAt", description="Timestamp when the bypass rule was created."
    )
    actor_id: PropertyRef = PropertyRef(
        "ActorId", description="ID of the user who created the bypass rule."
    )
    project_id_api: PropertyRef = PropertyRef(
        "ProjectId", description="Project ID returned by the Vercel API."
    )
    is_project_rule: PropertyRef = PropertyRef(
        "IsProjectRule", description="Whether the bypass rule is scoped to a project."
    )


@dataclass(frozen=True)
class VercelFirewallBypassToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:VercelProject)-[:RESOURCE]->(:VercelFirewallBypassRule)
class VercelFirewallBypassToProjectRel(CartographyRelSchema):
    """The Vercel project contains this firewall bypass rule as a resource."""

    target_node_label: str = "VercelProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("project_id", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: VercelFirewallBypassToProjectRelProperties = (
        VercelFirewallBypassToProjectRelProperties()
    )


@dataclass(frozen=True)
class VercelFirewallBypassToUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:VercelFirewallBypassRule)-[:CREATED_BY]->(:VercelUser)
class VercelFirewallBypassToUserRel(CartographyRelSchema):
    """The Vercel firewall bypass rule was created by this user."""

    target_node_label: str = "VercelUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ActorId")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CREATED_BY"
    properties: VercelFirewallBypassToUserRelProperties = (
        VercelFirewallBypassToUserRelProperties()
    )


@dataclass(frozen=True)
class VercelFirewallBypassRuleSchema(CartographyNodeSchema):
    """A Vercel firewall bypass rule that weakens firewall protections."""

    label: str = "VercelFirewallBypassRule"
    properties: VercelFirewallBypassRuleNodeProperties = (
        VercelFirewallBypassRuleNodeProperties()
    )
    sub_resource_relationship: VercelFirewallBypassToProjectRel = (
        VercelFirewallBypassToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [VercelFirewallBypassToUserRel()],
    )
