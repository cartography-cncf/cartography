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
    id: PropertyRef = PropertyRef("Id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    domain: PropertyRef = PropertyRef("Domain")
    ip: PropertyRef = PropertyRef("Ip")
    note: PropertyRef = PropertyRef("Note")
    action: PropertyRef = PropertyRef("Action")
    created_at: PropertyRef = PropertyRef("CreatedAt")
    actor_id: PropertyRef = PropertyRef("ActorId")
    project_id_api: PropertyRef = PropertyRef("ProjectId")
    is_project_rule: PropertyRef = PropertyRef("IsProjectRule")


@dataclass(frozen=True)
class VercelFirewallBypassToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:VercelProject)-[:RESOURCE]->(:VercelFirewallBypassRule)
class VercelFirewallBypassToProjectRel(CartographyRelSchema):
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
