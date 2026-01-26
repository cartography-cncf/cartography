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
class AzureFirewallProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")
    location: PropertyRef = PropertyRef("location")
    type: PropertyRef = PropertyRef("type")
    etag: PropertyRef = PropertyRef("etag")
    provisioning_state: PropertyRef = PropertyRef("provisioning_state")
    threat_intel_mode: PropertyRef = PropertyRef("threat_intel_mode")
    sku_name: PropertyRef = PropertyRef("sku_name")
    sku_tier: PropertyRef = PropertyRef("sku_tier")
    firewall_policy_id: PropertyRef = PropertyRef("firewall_policy_id")
    virtual_hub_id: PropertyRef = PropertyRef("virtual_hub_id")
    vnet_id: PropertyRef = PropertyRef("vnet_id")
    zones: PropertyRef = PropertyRef("zones")
    tags: PropertyRef = PropertyRef("tags")
    extended_location_name: PropertyRef = PropertyRef("extended_location_name")
    extended_location_type: PropertyRef = PropertyRef("extended_location_type")
    hub_private_ip_address: PropertyRef = PropertyRef("hub_private_ip_address")
    hub_public_ip_count: PropertyRef = PropertyRef("hub_public_ip_count")
    ip_groups_count: PropertyRef = PropertyRef("ip_groups_count")
    autoscale_min_capacity: PropertyRef = PropertyRef("autoscale_min_capacity")
    autoscale_max_capacity: PropertyRef = PropertyRef("autoscale_max_capacity")
    additional_properties: PropertyRef = PropertyRef("additional_properties")
    has_management_ip: PropertyRef = PropertyRef("has_management_ip")
    ip_configuration_count: PropertyRef = PropertyRef("ip_configuration_count")
    application_rule_collection_count: PropertyRef = PropertyRef(
        "application_rule_collection_count"
    )
    nat_rule_collection_count: PropertyRef = PropertyRef("nat_rule_collection_count")
    network_rule_collection_count: PropertyRef = PropertyRef(
        "network_rule_collection_count"
    )

    # IP Configurations - captures public IPs and subnet assignments
    ip_configurations: PropertyRef = PropertyRef("ip_configurations")
    management_ip_configuration: PropertyRef = PropertyRef(
        "management_ip_configuration"
    )

    # Rule Collections - actual firewall rules with ports, addresses, protocols
    network_rule_collections: PropertyRef = PropertyRef("network_rule_collections")
    application_rule_collections: PropertyRef = PropertyRef(
        "application_rule_collections"
    )
    nat_rule_collections: PropertyRef = PropertyRef("nat_rule_collections")

    # IP Groups - collections of IP addresses/ranges used in firewall rules
    ip_groups_detail: PropertyRef = PropertyRef("ip_groups_detail")


@dataclass(frozen=True)
class AzureFirewallToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureFirewallToSubscriptionRel(CartographyRelSchema):
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
    label: str = "AzureFirewall"
    properties: AzureFirewallProperties = AzureFirewallProperties()
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
