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
from cartography.models.ontology.labels import NETWORK_ACCESS_CONTROL


@dataclass(frozen=True)
class AzureFirewallProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Azure resource ID of the firewall."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", description="Name of the firewall.")
    location: PropertyRef = PropertyRef(
        "location", description="Azure region containing the firewall."
    )
    type: PropertyRef = PropertyRef(
        "type", description="Azure resource type of the firewall."
    )
    etag: PropertyRef = PropertyRef(
        "etag", description="Entity tag that changes when the firewall is updated."
    )
    provisioning_state: PropertyRef = PropertyRef(
        "provisioning_state", description="Current provisioning state of the firewall."
    )
    threat_intel_mode: PropertyRef = PropertyRef(
        "threat_intel_mode",
        description="Operating mode for threat intelligence filtering.",
    )
    sku_name: PropertyRef = PropertyRef(
        "sku_name", description="Name of the firewall SKU."
    )
    sku_tier: PropertyRef = PropertyRef(
        "sku_tier", description="Tier of the firewall SKU."
    )
    firewall_policy_id: PropertyRef = PropertyRef(
        "firewall_policy_id",
        description="Azure resource ID of the associated firewall policy.",
    )
    virtual_hub_id: PropertyRef = PropertyRef(
        "virtual_hub_id",
        description="Azure resource ID of the virtual hub hosting the firewall.",
    )
    vnet_id: PropertyRef = PropertyRef(
        "vnet_id",
        description="Azure resource ID of the virtual network hosting the firewall.",
    )
    zones: PropertyRef = PropertyRef(
        "zones", description="Availability zones assigned to the firewall."
    )
    tags: PropertyRef = PropertyRef(
        "tags", description="Azure resource tags assigned to the firewall."
    )
    extended_location_name: PropertyRef = PropertyRef(
        "extended_location_name", description="Name of the firewall extended location."
    )
    extended_location_type: PropertyRef = PropertyRef(
        "extended_location_type", description="Type of the firewall extended location."
    )
    hub_private_ip_address: PropertyRef = PropertyRef(
        "hub_private_ip_address",
        description="Private IP address assigned to the secured virtual hub.",
    )
    hub_public_ip_count: PropertyRef = PropertyRef(
        "hub_public_ip_count",
        description="Number of public IP addresses assigned to the secured virtual hub.",
    )
    ip_groups_count: PropertyRef = PropertyRef(
        "ip_groups_count", description="Number of IP groups referenced by the firewall."
    )
    autoscale_min_capacity: PropertyRef = PropertyRef(
        "autoscale_min_capacity",
        description="Minimum autoscale capacity of the firewall.",
    )
    autoscale_max_capacity: PropertyRef = PropertyRef(
        "autoscale_max_capacity",
        description="Maximum autoscale capacity of the firewall.",
    )
    additional_properties: PropertyRef = PropertyRef(
        "additional_properties",
        description="Additional Azure properties associated with the firewall.",
    )
    has_management_ip: PropertyRef = PropertyRef(
        "has_management_ip",
        description="Whether the firewall has a management IP configuration.",
    )
    ip_configuration_count: PropertyRef = PropertyRef(
        "ip_configuration_count",
        description="Number of IP configurations on the firewall.",
    )
    application_rule_collection_count: PropertyRef = PropertyRef(
        "application_rule_collection_count",
        description="Number of application rule collections on the firewall.",
    )
    nat_rule_collection_count: PropertyRef = PropertyRef(
        "nat_rule_collection_count",
        description="Number of NAT rule collections on the firewall.",
    )
    network_rule_collection_count: PropertyRef = PropertyRef(
        "network_rule_collection_count",
        description="Number of network rule collections on the firewall.",
    )

    # IP Configurations - captures public IPs and subnet assignments
    ip_configurations: PropertyRef = PropertyRef(
        "ip_configurations", description="IP configurations assigned to the firewall."
    )
    management_ip_configuration: PropertyRef = PropertyRef(
        "management_ip_configuration",
        description="Management IP configuration assigned to the firewall.",
    )

    # Rule Collections - actual firewall rules with ports, addresses, protocols
    network_rule_collections: PropertyRef = PropertyRef(
        "network_rule_collections",
        description="Network rule collections configured on the firewall.",
    )
    application_rule_collections: PropertyRef = PropertyRef(
        "application_rule_collections",
        description="Application rule collections configured on the firewall.",
    )
    nat_rule_collections: PropertyRef = PropertyRef(
        "nat_rule_collections",
        description="NAT rule collections configured on the firewall.",
    )

    # IP Groups - collections of IP addresses/ranges used in firewall rules
    ip_groups_detail: PropertyRef = PropertyRef(
        "ip_groups_detail",
        description="Details of IP groups referenced by the firewall.",
    )


@dataclass(frozen=True)
class AzureFirewallToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureFirewallToSubscriptionRel(CartographyRelSchema):
    """An Azure subscription contains the firewall as a resource."""

    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureFirewallToSubscriptionRelProperties = (
        AzureFirewallToSubscriptionRelProperties()
    )


@dataclass(frozen=True)
class AzureFirewallToVirtualNetworkRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureFirewallToVirtualNetworkRel(CartographyRelSchema):
    """An Azure Firewall belongs to a virtual network."""

    target_node_label: str = "AzureVirtualNetwork"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("vnet_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF"
    properties: AzureFirewallToVirtualNetworkRelProperties = (
        AzureFirewallToVirtualNetworkRelProperties()
    )


@dataclass(frozen=True)
class AzureFirewallToVirtualHubRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureFirewallToVirtualHubRel(CartographyRelSchema):
    """An Azure Firewall is deployed to a virtual hub."""

    target_node_label: str = "AzureVirtualHub"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("virtual_hub_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "DEPLOYED_TO"
    properties: AzureFirewallToVirtualHubRelProperties = (
        AzureFirewallToVirtualHubRelProperties()
    )


@dataclass(frozen=True)
class AzureFirewallToFirewallPolicyRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureFirewallToFirewallPolicyRel(CartographyRelSchema):
    """An Azure Firewall uses a firewall policy."""

    target_node_label: str = "AzureFirewallPolicy"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("firewall_policy_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_POLICY"
    properties: AzureFirewallToFirewallPolicyRelProperties = (
        AzureFirewallToFirewallPolicyRelProperties()
    )


@dataclass(frozen=True)
class AzureFirewallSchema(CartographyNodeSchema):
    """An Azure Firewall that filters network traffic."""

    label: str = "AzureFirewall"
    properties: AzureFirewallProperties = AzureFirewallProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([NETWORK_ACCESS_CONTROL])
    sub_resource_relationship: AzureFirewallToSubscriptionRel = (
        AzureFirewallToSubscriptionRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AzureFirewallToVirtualNetworkRel(),
            AzureFirewallToVirtualHubRel(),
            AzureFirewallToFirewallPolicyRel(),
        ],
    )
