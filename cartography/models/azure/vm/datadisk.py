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
class AzureDataDiskProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "managed_disk.id", description="Azure resource ID of the managed disk."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", description="Name of the data disk.")
    lun: PropertyRef = PropertyRef(
        "lun", description="Logical unit number of the data disk."
    )
    vhd: PropertyRef = PropertyRef(
        "vhd.uri", description="URI of the virtual hard disk."
    )
    image: PropertyRef = PropertyRef(
        "image.uri", description="URI of the source image."
    )
    size: PropertyRef = PropertyRef(
        "disk_size_gb", description="Size of the data disk in GB."
    )
    caching: PropertyRef = PropertyRef(
        "caching", description="Host caching mode for the data disk."
    )
    createoption: PropertyRef = PropertyRef(
        "create_option", description="Source used to create or attach the data disk."
    )
    write_accelerator_enabled: PropertyRef = PropertyRef(
        "write_accelerator_enabled",
        description="Whether Write Accelerator is enabled for the data disk.",
    )
    managed_disk_storage_type: PropertyRef = PropertyRef(
        "managed_disk.storage_account_type",
        description="Storage account type of the managed disk.",
    )


@dataclass(frozen=True)
class AzureDataDiskToVirtualMachineRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureVirtualMachine)-[:ATTACHED_TO]->(:AzureDataDisk)
class AzureDataDiskToVirtualMachineRel(CartographyRelSchema):
    """An Azure virtual machine has the data disk attached."""

    target_node_label: str = "AzureVirtualMachine"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("vm_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "ATTACHED_TO"
    properties: AzureDataDiskToVirtualMachineRelProperties = (
        AzureDataDiskToVirtualMachineRelProperties()
    )


@dataclass(frozen=True)
class AzureDataDiskToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureSubscription)-[:RESOURCE]->(:AzureDataDisk)
class AzureDataDiskToSubscriptionRel(CartographyRelSchema):
    """An Azure subscription contains the data disk as a resource."""

    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureDataDiskToSubscriptionRelProperties = (
        AzureDataDiskToSubscriptionRelProperties()
    )


@dataclass(frozen=True)
class AzureDataDiskSchema(CartographyNodeSchema):
    """A data disk attached to an Azure virtual machine."""

    label: str = "AzureDataDisk"
    properties: AzureDataDiskProperties = AzureDataDiskProperties()
    sub_resource_relationship: AzureDataDiskToSubscriptionRel = (
        AzureDataDiskToSubscriptionRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AzureDataDiskToVirtualMachineRel(),
        ]
    )
