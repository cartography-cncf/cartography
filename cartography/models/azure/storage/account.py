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
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    type: PropertyRef = PropertyRef("type")
    resourcegroup: PropertyRef = PropertyRef("resourceGroup")
    location: PropertyRef = PropertyRef("location")
    kind: PropertyRef = PropertyRef("kind")
    name: PropertyRef = PropertyRef("name")
    creationtime: PropertyRef = PropertyRef("creation_time")
    hnsenabled: PropertyRef = PropertyRef("is_hns_enabled")
    primarylocation: PropertyRef = PropertyRef("primary_location")
    secondarylocation: PropertyRef = PropertyRef("secondary_location")
    provisioningstate: PropertyRef = PropertyRef("provisioning_state")
    statusofprimary: PropertyRef = PropertyRef("status_of_primary")
    statusofsecondary: PropertyRef = PropertyRef("status_of_secondary")
    supportshttpstrafficonly: PropertyRef = PropertyRef(
        "enable_https_traffic_only",
    )


@dataclass(frozen=True)
class AzureStorageAccountToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureSubscription)-[:RESOURCE]->(:AzureStorageAccount)
class AzureStorageAccountToSubscriptionRel(CartographyRelSchema):
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
    label: str = "AzureStorageAccount"
    properties: AzureStorageAccountProperties = AzureStorageAccountProperties()
    sub_resource_relationship: AzureStorageAccountToSubscriptionRel = (
        AzureStorageAccountToSubscriptionRel()
    )
