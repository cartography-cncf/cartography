import logging
from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AzurePublicIPAddressProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Full Azure resource ID of the public IP address."
    )
    name: PropertyRef = PropertyRef(
        "name", description="Name of the public IP address resource."
    )
    location: PropertyRef = PropertyRef(
        "location",
        description="Azure region where the public IP address is deployed.",
    )
    ip_address: PropertyRef = PropertyRef(
        "ip_address", description="Assigned public IP address."
    )
    allocation_method: PropertyRef = PropertyRef(
        "public_ip_allocation_method",
        description="Public IP allocation method.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzurePublicIPAddressToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzurePublicIPAddressToSubscriptionRel(CartographyRelSchema):
    """An Azure subscription contains the public IP address as a resource."""

    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzurePublicIPAddressToSubscriptionRelProperties = (
        AzurePublicIPAddressToSubscriptionRelProperties()
    )


@dataclass(frozen=True)
class AzurePublicIPAddressSchema(CartographyNodeSchema):
    """A public IP address resource in Azure."""

    label: str = "AzurePublicIPAddress"
    properties: AzurePublicIPAddressProperties = AzurePublicIPAddressProperties()
    sub_resource_relationship: AzurePublicIPAddressToSubscriptionRel = (
        AzurePublicIPAddressToSubscriptionRel()
    )
