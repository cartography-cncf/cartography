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
class AzureDiskProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")
    location: PropertyRef = PropertyRef("location")
    resourcegroup: PropertyRef = PropertyRef("resource_group")
    type: PropertyRef = PropertyRef("type")
    createoption: PropertyRef = PropertyRef("creation_data.create_option")
    disksizegb: PropertyRef = PropertyRef("disk_size_gb")
    encryption: PropertyRef = PropertyRef("encryption_settings_collection.enabled")
    maxshares: PropertyRef = PropertyRef("max_shares")
    network_access_policy: PropertyRef = PropertyRef("network_access_policy")
    ostype: PropertyRef = PropertyRef("os_type")
    tier: PropertyRef = PropertyRef("tier")
    sku: PropertyRef = PropertyRef("sku.name")
    zones: PropertyRef = PropertyRef("zones")


@dataclass(frozen=True)
class AzureDiskToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureSubscription)-[:RESOURCE]->(:AzureDisk)
class AzureDiskToSubscriptionRel(CartographyRelSchema):
    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureDiskToSubscriptionRelProperties = (
        AzureDiskToSubscriptionRelProperties()
    )


@dataclass(frozen=True)
class AzureDiskSchema(CartographyNodeSchema):
    label: str = "AzureDisk"
    properties: AzureDiskProperties = AzureDiskProperties()
    sub_resource_relationship: AzureDiskToSubscriptionRel = AzureDiskToSubscriptionRel()
