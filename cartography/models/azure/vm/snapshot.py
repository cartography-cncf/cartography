from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.ontology.labels import SNAPSHOT


@dataclass(frozen=True)
class AzureSnapshotProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Azure resource ID of the snapshot."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    resourcegroup: PropertyRef = PropertyRef(
        "resource_group", description="Resource group containing the snapshot."
    )
    type: PropertyRef = PropertyRef(
        "type", description="Azure resource type of the snapshot."
    )
    location: PropertyRef = PropertyRef(
        "location", description="Azure region of the snapshot."
    )
    name: PropertyRef = PropertyRef("name", description="Name of the snapshot.")
    createoption: PropertyRef = PropertyRef(
        "creation_data.create_option",
        description="Source used to create the snapshot.",
    )
    disksizegb: PropertyRef = PropertyRef(
        "disk_size_gb", description="Size of the snapshot in GB."
    )
    encryption: PropertyRef = PropertyRef(
        "encryption_settings_collection.enabled",
        description="Whether Azure Disk Encryption settings are enabled.",
    )
    incremental: PropertyRef = PropertyRef(
        "incremental", description="Whether the snapshot is incremental."
    )
    network_access_policy: PropertyRef = PropertyRef(
        "network_access_policy",
        description="Policy governing network access to the snapshot.",
    )
    ostype: PropertyRef = PropertyRef(
        "os_type", description="Operating system type of the snapshot."
    )
    tier: PropertyRef = PropertyRef(
        "tier", description="Performance tier of the snapshot."
    )
    sku: PropertyRef = PropertyRef("sku.name", description="SKU name of the snapshot.")


@dataclass(frozen=True)
class AzureSnapshotToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureSubscription)-[:RESOURCE]->(:AzureSnapshot)
class AzureSnapshotToSubscriptionRel(CartographyRelSchema):
    """An Azure subscription contains the snapshot as a resource."""

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
    """An Azure point-in-time managed disk snapshot."""

    label: str = "AzureSnapshot"
    properties: AzureSnapshotProperties = AzureSnapshotProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([SNAPSHOT])
    sub_resource_relationship: AzureSnapshotToSubscriptionRel = (
        AzureSnapshotToSubscriptionRel()
    )
