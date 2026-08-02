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
class CloudflareFirewallRuleNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    action: PropertyRef = PropertyRef("action")
    description: PropertyRef = PropertyRef("description")
    paused: PropertyRef = PropertyRef("paused")
    priority: PropertyRef = PropertyRef("priority")
    products: PropertyRef = PropertyRef("products")
    ref: PropertyRef = PropertyRef("ref")
    filter_id: PropertyRef = PropertyRef("filter_id")
    filter_description: PropertyRef = PropertyRef("filter_description")
    filter_expression: PropertyRef = PropertyRef("filter_expression")
    filter_paused: PropertyRef = PropertyRef("filter_paused")
    filter_ref: PropertyRef = PropertyRef("filter_ref")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class CloudflareFirewallRuleToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:CloudflareFirewallRule)<-[:RESOURCE]-(:CloudflareAccount)
class CloudflareFirewallRuleToAccountRel(CartographyRelSchema):
    target_node_label: str = "CloudflareAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("account_id", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: CloudflareFirewallRuleToAccountRelProperties = (
        CloudflareFirewallRuleToAccountRelProperties()
    )


@dataclass(frozen=True)
class CloudflareFirewallRuleToZoneRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:CloudflareZone)-[:HAS_FIREWALL_RULE]->(:CloudflareFirewallRule)
class CloudflareFirewallRuleToZoneRel(CartographyRelSchema):
    target_node_label: str = "CloudflareZone"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("zone_id", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_FIREWALL_RULE"
    properties: CloudflareFirewallRuleToZoneRelProperties = (
        CloudflareFirewallRuleToZoneRelProperties()
    )


@dataclass(frozen=True)
class CloudflareFirewallRuleSchema(CartographyNodeSchema):
    label: str = "CloudflareFirewallRule"
    properties: CloudflareFirewallRuleNodeProperties = (
        CloudflareFirewallRuleNodeProperties()
    )
    sub_resource_relationship: CloudflareFirewallRuleToAccountRel = (
        CloudflareFirewallRuleToAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            CloudflareFirewallRuleToZoneRel(),
        ]
    )
