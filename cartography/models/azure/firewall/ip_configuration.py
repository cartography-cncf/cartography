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

    id: PropertyRef = PropertyRef(
        "id", description="Azure resource ID of the firewall IP configuration."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", description="Name of the firewall IP configuration."
    )
    private_ip_address: PropertyRef = PropertyRef(
        "private_ip_address",
        description="Private IP address assigned to the configuration.",
    )
    private_ip_allocation_method: PropertyRef = PropertyRef(
        "private_ip_allocation_method",
        description="Allocation method for the private IP address.",
    )
    provisioning_state: PropertyRef = PropertyRef(
        "provisioning_state",
        description="Current provisioning state of the IP configuration.",
    )
    type: PropertyRef = PropertyRef(
        "type", description="Azure resource type of the IP configuration."
    )
    etag: PropertyRef = PropertyRef(
        "etag",
        description="Entity tag that changes when the IP configuration is updated.",
    )
    subnet_id: PropertyRef = PropertyRef(
        "subnet_id", description="Azure resource ID of the associated subnet."
    )
    public_ip_address_id: PropertyRef = PropertyRef(
        "public_ip_address_id",
        description="Azure resource ID of the associated public IP address.",
    )
    firewall_id: PropertyRef = PropertyRef(
        "firewall_id",
        description="Azure resource ID of the firewall that owns the configuration.",
    )


@dataclass(frozen=True)
class AzureFirewallIPConfigurationToAzureSubscriptionRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureFirewallIPConfigurationToAzureSubscriptionRel(CartographyRelSchema):
    """An Azure subscription contains the firewall IP configuration as a resource."""

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
    """An Azure Firewall has the IP configuration."""

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
    """An Azure Firewall IP configuration is assigned to a subnet."""

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
    """An Azure Firewall IP configuration uses a public IP address."""

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
    """An IP configuration assigned to an Azure Firewall."""

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
