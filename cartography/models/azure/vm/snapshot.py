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
class AzureSnapshotProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    resourcegroup: PropertyRef = PropertyRef("resource_group")
    type: PropertyRef = PropertyRef("type")
    location: PropertyRef = PropertyRef("location")
    name: PropertyRef = PropertyRef("name")
    createoption: PropertyRef = PropertyRef("creation_data.create_option")
    disksizegb: PropertyRef = PropertyRef("disk_size_gb")
    encryption: PropertyRef = PropertyRef("encryption_settings_collection.enabled")
    incremental: PropertyRef = PropertyRef("incremental")
    network_access_policy: PropertyRef = PropertyRef("network_access_policy")
    ostype: PropertyRef = PropertyRef("os_type")
    tier: PropertyRef = PropertyRef("tier")
    sku: PropertyRef = PropertyRef("sku.name")


@dataclass(frozen=True)
class AzureSnapshotToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureSubscription)-[:RESOURCE]->(:AzureSnapshot)
class AzureSnapshotToSubscriptionRel(CartographyRelSchema):
    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureSnapshotToSubscriptionRelProperties = (
        AzureSnapshotToSubscriptionRelProperties()
    )


@dataclass(frozen=True)
class AzureSnapshotSchema(CartographyNodeSchema):
    label: str = "AzureSnapshot"
    properties: AzureSnapshotProperties = AzureSnapshotProperties()
    sub_resource_relationship: AzureSnapshotToSubscriptionRel = (
        AzureSnapshotToSubscriptionRel()
    )
