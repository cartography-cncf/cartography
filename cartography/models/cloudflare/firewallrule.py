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
    id: PropertyRef = PropertyRef("id", description="Firewall rule ID.")
    action: PropertyRef = PropertyRef(
        "action",
        description="Action applied to matched traffic, such as block or allow.",
    )
    description: PropertyRef = PropertyRef(
        "description",
        description="A note about why the rule exists, if any.",
    )
    paused: PropertyRef = PropertyRef(
        "paused",
        description="Whether the rule is currently paused.",
    )
    priority: PropertyRef = PropertyRef(
        "priority",
        description="Order in which the rule is evaluated.",
    )
    products: PropertyRef = PropertyRef(
        "products",
        description="Cloudflare products the rule applies to.",
    )
    ref: PropertyRef = PropertyRef(
        "ref",
        description="Short identifier used for logging.",
    )
    filter_id: PropertyRef = PropertyRef(
        "filter_id",
        description="Identifier of the rule's filter expression.",
    )
    filter_description: PropertyRef = PropertyRef(
        "filter_description",
        description="A note about the filter expression, if any.",
    )
    filter_expression: PropertyRef = PropertyRef(
        "filter_expression",
        description="Expression that traffic must match for the rule to apply.",
    )
    filter_paused: PropertyRef = PropertyRef(
        "filter_paused",
        description="Whether the filter is currently paused.",
    )
    filter_ref: PropertyRef = PropertyRef(
        "filter_ref",
        description="Short identifier for the filter, if any.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class CloudflareFirewallRuleToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:CloudflareFirewallRule)<-[:RESOURCE]-(:CloudflareAccount)
class CloudflareFirewallRuleToAccountRel(CartographyRelSchema):
    """The account contains the firewall rule."""

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
    """The DNS zone contains the firewall rule."""

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
    """A zone-level firewall rule in Cloudflare."""

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
