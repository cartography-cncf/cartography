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
class AzureNetworkSecurityRuleProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    description: PropertyRef = PropertyRef("description")
    protocol: PropertyRef = PropertyRef("protocol")
    direction: PropertyRef = PropertyRef("direction")
    access: PropertyRef = PropertyRef("access")
    priority: PropertyRef = PropertyRef("priority")
    source_port_range: PropertyRef = PropertyRef("source_port_range")
    source_port_ranges: PropertyRef = PropertyRef("source_port_ranges")
    destination_port_range: PropertyRef = PropertyRef("destination_port_range")
    destination_port_ranges: PropertyRef = PropertyRef("destination_port_ranges")
    source_address_prefix: PropertyRef = PropertyRef("source_address_prefix")
    source_address_prefixes: PropertyRef = PropertyRef("source_address_prefixes")
    destination_address_prefix: PropertyRef = PropertyRef("destination_address_prefix")
    destination_address_prefixes: PropertyRef = PropertyRef(
        "destination_address_prefixes"
    )
    is_default: PropertyRef = PropertyRef("is_default")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureNetworkSecurityRuleToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureSubscription)-[:RESOURCE]->(:AzureNetworkSecurityRule)
class AzureNetworkSecurityRuleToSubscriptionRel(CartographyRelSchema):
    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureNetworkSecurityRuleToSubscriptionRelProperties = (
        AzureNetworkSecurityRuleToSubscriptionRelProperties()
    )


@dataclass(frozen=True)
class AzureNetworkSecurityRuleToNSGRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureNetworkSecurityRule)-[:MEMBER_OF_AZURE_NSG]->(:AzureNetworkSecurityGroup)
class AzureNetworkSecurityRuleToNSGRel(CartographyRelSchema):
    target_node_label: str = "AzureNetworkSecurityGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("nsg_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF_AZURE_NSG"
    properties: AzureNetworkSecurityRuleToNSGRelProperties = (
        AzureNetworkSecurityRuleToNSGRelProperties()
    )


@dataclass(frozen=True)
class AzureInboundNetworkSecurityRuleSchema(CartographyNodeSchema):
    """Schema for inbound NSG rules. Carries the cross-cloud `IpRule` and
    `IpPermissionInbound` semantic labels so it can be matched alongside
    AWS / GCP equivalents."""

    label: str = "AzureNetworkSecurityRule"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        ["IpPermissionInbound", "IpRule"]
    )
    properties: AzureNetworkSecurityRuleProperties = (
        AzureNetworkSecurityRuleProperties()
    )
    sub_resource_relationship: AzureNetworkSecurityRuleToSubscriptionRel = (
        AzureNetworkSecurityRuleToSubscriptionRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AzureNetworkSecurityRuleToNSGRel(),
        ],
    )


@dataclass(frozen=True)
class AzureOutboundNetworkSecurityRuleSchema(CartographyNodeSchema):
    """Schema for outbound NSG rules. Carries the cross-cloud `IpRule` and
    `IpPermissionEgress` semantic labels."""

    label: str = "AzureNetworkSecurityRule"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        ["IpPermissionEgress", "IpRule"]
    )
    properties: AzureNetworkSecurityRuleProperties = (
        AzureNetworkSecurityRuleProperties()
    )
    sub_resource_relationship: AzureNetworkSecurityRuleToSubscriptionRel = (
        AzureNetworkSecurityRuleToSubscriptionRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AzureNetworkSecurityRuleToNSGRel(),
        ],
    )
