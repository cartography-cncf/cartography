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
class AzureFirewallIPConfigurationProperties(CartographyNodeProperties):
    """
    Properties for Azure Firewall IP Configuration nodes
    """

    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")
    private_ip_address: PropertyRef = PropertyRef("private_ip_address")
    private_ip_allocation_method: PropertyRef = PropertyRef(
        "private_ip_allocation_method"
    )
    provisioning_state: PropertyRef = PropertyRef("provisioning_state")
    type: PropertyRef = PropertyRef("type")
    etag: PropertyRef = PropertyRef("etag")
    subnet_id: PropertyRef = PropertyRef("subnet_id")
    public_ip_address_id: PropertyRef = PropertyRef("public_ip_address_id")
    firewall_id: PropertyRef = PropertyRef("firewall_id")


@dataclass(frozen=True)
class AzureFirewallIPConfigurationToAzureSubscriptionRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureFirewallIPConfigurationToAzureSubscriptionRel(CartographyRelSchema):
    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureFirewallIPConfigurationToAzureSubscriptionRelProperties = (
        AzureFirewallIPConfigurationToAzureSubscriptionRelProperties()
    )


@dataclass(frozen=True)
class AzureFirewallIPConfigurationToAzureFirewallRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureFirewallIPConfigurationToAzureFirewallRel(CartographyRelSchema):
    target_node_label: str = "AzureFirewall"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("firewall_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_IP_CONFIGURATION"
    properties: AzureFirewallIPConfigurationToAzureFirewallRelProperties = (
        AzureFirewallIPConfigurationToAzureFirewallRelProperties()
    )


@dataclass(frozen=True)
class AzureFirewallIPConfigurationToSubnetRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureFirewallIPConfigurationToSubnetRel(CartographyRelSchema):
    target_node_label: str = "AzureSubnet"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("subnet_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "IN_SUBNET"
    properties: AzureFirewallIPConfigurationToSubnetRelProperties = (
        AzureFirewallIPConfigurationToSubnetRelProperties()
    )


@dataclass(frozen=True)
class AzureFirewallIPConfigurationToPublicIPRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureFirewallIPConfigurationToPublicIPRel(CartographyRelSchema):
    target_node_label: str = "AzurePublicIPAddress"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("public_ip_address_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_PUBLIC_IP"
    properties: AzureFirewallIPConfigurationToPublicIPRelProperties = (
        AzureFirewallIPConfigurationToPublicIPRelProperties()
    )


@dataclass(frozen=True)
class AzureFirewallIPConfigurationSchema(CartographyNodeSchema):
    label: str = "AzureFirewallIPConfiguration"
    properties: AzureFirewallIPConfigurationProperties = (
        AzureFirewallIPConfigurationProperties()
    )
    sub_resource_relationship: AzureFirewallIPConfigurationToAzureSubscriptionRel = (
        AzureFirewallIPConfigurationToAzureSubscriptionRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AzureFirewallIPConfigurationToAzureFirewallRel(),
            AzureFirewallIPConfigurationToSubnetRel(),
            AzureFirewallIPConfigurationToPublicIPRel(),
        ],
    )
