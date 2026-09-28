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
from cartography.models.ontology.labels import BLOCK_STORAGE


@dataclass(frozen=True)
class AzureDiskProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Azure resource ID of the managed disk."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", description="Name of the managed disk.")
    location: PropertyRef = PropertyRef(
        "location", description="Azure region of the managed disk."
    )
    resourcegroup: PropertyRef = PropertyRef(
        "resource_group", description="Resource group containing the managed disk."
    )
    type: PropertyRef = PropertyRef(
        "type", description="Azure resource type of the managed disk."
    )
    createoption: PropertyRef = PropertyRef(
        "creation_data.create_option",
        description="Source used to create the managed disk.",
    )
    disksizegb: PropertyRef = PropertyRef(
        "disk_size_gb", description="Size of the managed disk in GB."
    )
    encryption: PropertyRef = PropertyRef(
        "encryption_settings_collection.enabled",
        description="Whether Azure Disk Encryption settings are enabled.",
    )
    maxshares: PropertyRef = PropertyRef(
        "max_shares",
        description="Maximum number of virtual machines that can attach to the disk.",
    )
    network_access_policy: PropertyRef = PropertyRef(
        "network_access_policy",
        description="Policy governing network access to the disk.",
    )
    ostype: PropertyRef = PropertyRef(
        "os_type", description="Operating system type of the disk."
    )
    state: PropertyRef = PropertyRef(
        "disk_state", description="Current lifecycle state of the disk."
    )
    tier: PropertyRef = PropertyRef("tier", description="Performance tier of the disk.")
    sku: PropertyRef = PropertyRef("sku.name", description="SKU name of the disk.")
    zones: PropertyRef = PropertyRef(
        "zones", description="Availability zones of the disk."
    )


@dataclass(frozen=True)
class AzureDiskToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureSubscription)-[:RESOURCE]->(:AzureDisk)
class AzureDiskToSubscriptionRel(CartographyRelSchema):
    """An Azure subscription contains the managed disk as a resource."""

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
    """An Azure managed disk."""

    label: str = "AzureDisk"
    properties: AzureDiskProperties = AzureDiskProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([BLOCK_STORAGE])
    sub_resource_relationship: AzureDiskToSubscriptionRel = AzureDiskToSubscriptionRel()
