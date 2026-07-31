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
from cartography.models.extra_labels import IP_PERMISSION_EGRESS
from cartography.models.extra_labels import IP_PERMISSION_INBOUND
from cartography.models.extra_labels import IP_RULE


@dataclass(frozen=True)
class AzureNetworkSecurityRuleProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Full Azure resource ID of the security rule."
    )
    name: PropertyRef = PropertyRef("name", description="Name of the security rule.")
    description: PropertyRef = PropertyRef(
        "description", description="Description configured for the security rule."
    )
    protocol: PropertyRef = PropertyRef(
        "protocol", description="Network protocol matched by the rule."
    )
    direction: PropertyRef = PropertyRef(
        "direction", description="Traffic direction matched by the rule."
    )
    access: PropertyRef = PropertyRef(
        "access", description="Whether matching traffic is allowed or denied."
    )
    priority: PropertyRef = PropertyRef(
        "priority", description="Evaluation priority of the rule."
    )
    source_port_range: PropertyRef = PropertyRef(
        "source_port_range", description="Single source port or port range."
    )
    source_port_ranges: PropertyRef = PropertyRef(
        "source_port_ranges", description="Source ports and port ranges."
    )
    destination_port_range: PropertyRef = PropertyRef(
        "destination_port_range", description="Single destination port or port range."
    )
    destination_port_ranges: PropertyRef = PropertyRef(
        "destination_port_ranges", description="Destination ports and port ranges."
    )
    source_address_prefix: PropertyRef = PropertyRef(
        "source_address_prefix", description="Single source address prefix."
    )
    source_address_prefixes: PropertyRef = PropertyRef(
        "source_address_prefixes", description="Source address prefixes."
    )
    destination_address_prefix: PropertyRef = PropertyRef(
        "destination_address_prefix", description="Single destination address prefix."
    )
    destination_address_prefixes: PropertyRef = PropertyRef(
        "destination_address_prefixes",
        description="Destination address prefixes.",
    )
    is_default: PropertyRef = PropertyRef(
        "is_default",
        description="Whether the rule is a default Azure security rule.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureNetworkSecurityRuleToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureSubscription)-[:RESOURCE]->(:AzureNetworkSecurityRule)
class AzureNetworkSecurityRuleToSubscriptionRel(CartographyRelSchema):
    """An Azure subscription contains the security rule as a resource."""

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
    """An Azure security rule belongs to a network security group."""

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
    """An inbound rule of an Azure network security group, carrying the
    `IpPermissionInbound` label so it matches AWS and GCP ingress rules."""

    label: str = "AzureNetworkSecurityRule"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [IP_PERMISSION_INBOUND, IP_RULE]
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
    """An outbound rule of an Azure network security group, carrying the
    `IpPermissionEgress` label so it matches AWS and GCP egress rules."""

    label: str = "AzureNetworkSecurityRule"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [IP_PERMISSION_EGRESS, IP_RULE]
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
