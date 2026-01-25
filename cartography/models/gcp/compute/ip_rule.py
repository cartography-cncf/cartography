from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class GCPIpRuleNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("ruleid")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    protocol: PropertyRef = PropertyRef("protocol")
    fromport: PropertyRef = PropertyRef("fromport")
    toport: PropertyRef = PropertyRef("toport")


@dataclass(frozen=True)
class GCPIpRuleToFirewallAllowedByRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPIpRuleToFirewallAllowedByRel(CartographyRelSchema):
    target_node_label: str = "GCPFirewall"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("fw_partial_uri"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ALLOWED_BY"
    properties: GCPIpRuleToFirewallAllowedByRelProperties = (
        GCPIpRuleToFirewallAllowedByRelProperties()
    )


@dataclass(frozen=True)
class GCPIpRuleToFirewallDeniedByRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPIpRuleToFirewallDeniedByRel(CartographyRelSchema):
    target_node_label: str = "GCPFirewall"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("fw_partial_uri"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "DENIED_BY"
    properties: GCPIpRuleToFirewallDeniedByRelProperties = (
        GCPIpRuleToFirewallDeniedByRelProperties()
    )


@dataclass(frozen=True)
class GCPIpRuleToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPIpRuleToProjectRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("PROJECT_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPIpRuleToProjectRelProperties = GCPIpRuleToProjectRelProperties()


@dataclass(frozen=True)
class GCPIpRuleAllowedSchema(CartographyNodeSchema):
    """Schema for IP rules that are allowed by a firewall."""

    label: str = "IpRule"
    properties: GCPIpRuleNodeProperties = GCPIpRuleNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        ["IpPermissionInbound", "GCPIpRule"]
    )
    sub_resource_relationship: GCPIpRuleToProjectRel = GCPIpRuleToProjectRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GCPIpRuleToFirewallAllowedByRel(),
        ]
    )


@dataclass(frozen=True)
class GCPIpRuleDeniedSchema(CartographyNodeSchema):
    """Schema for IP rules that are denied by a firewall."""

    label: str = "IpRule"
    properties: GCPIpRuleNodeProperties = GCPIpRuleNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        ["IpPermissionInbound", "GCPIpRule"]
    )
    sub_resource_relationship: GCPIpRuleToProjectRel = GCPIpRuleToProjectRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GCPIpRuleToFirewallDeniedByRel(),
        ]
    )
