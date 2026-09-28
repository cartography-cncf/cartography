from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class AzureStorageAccountProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Azure resource ID.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    type: PropertyRef = PropertyRef("type", description="Azure resource type.")
    resourcegroup: PropertyRef = PropertyRef(
        "resourceGroup",
        description="Name of the Azure resource group that contains the storage account.",
    )
    location: PropertyRef = PropertyRef(
        "location", description="Azure region where the storage account is located."
    )
    kind: PropertyRef = PropertyRef("kind", description="Type of storage account.")
    name: PropertyRef = PropertyRef("name", description="Azure resource name.")
    creationtime: PropertyRef = PropertyRef(
        "creation_time", description="Time when the storage account was created."
    )
    hnsenabled: PropertyRef = PropertyRef(
        "is_hns_enabled",
        description="Whether the hierarchical namespace is enabled for the storage account.",
    )
    primarylocation: PropertyRef = PropertyRef(
        "primary_location", description="Primary Azure region for the storage account."
    )
    secondarylocation: PropertyRef = PropertyRef(
        "secondary_location",
        description="Secondary Azure region for the storage account.",
    )
    provisioningstate: PropertyRef = PropertyRef(
        "provisioning_state", description="Provisioning state of the storage account."
    )
    statusofprimary: PropertyRef = PropertyRef(
        "status_of_primary", description="Availability status of the primary region."
    )
    statusofsecondary: PropertyRef = PropertyRef(
        "status_of_secondary",
        description="Availability status of the secondary region.",
    )
    supportshttpstrafficonly: PropertyRef = PropertyRef(
        "enable_https_traffic_only",
        description="Whether the storage account accepts only HTTPS traffic.",
    )


@dataclass(frozen=True)
class AzureStorageAccountToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureSubscription)-[:RESOURCE]->(:AzureStorageAccount)
class AzureStorageAccountToSubscriptionRel(CartographyRelSchema):
    """An Azure subscription contains the storage account as a resource."""

    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureStorageAccountToSubscriptionRelProperties = (
        AzureStorageAccountToSubscriptionRelProperties()
    )


@dataclass(frozen=True)
class AzureStorageAccountSchema(CartographyNodeSchema):
    """An Azure Storage account that provides blob, file, queue, and table services."""

    label: str = "AzureStorageAccount"
    properties: AzureStorageAccountProperties = AzureStorageAccountProperties()
    sub_resource_relationship: AzureStorageAccountToSubscriptionRel = (
        AzureStorageAccountToSubscriptionRel()
    )
