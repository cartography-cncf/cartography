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
    id: PropertyRef = PropertyRef("managed_disk.id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")
    lun: PropertyRef = PropertyRef("lun")
    vhd: PropertyRef = PropertyRef("vhd.uri")
    image: PropertyRef = PropertyRef("image.uri")
    size: PropertyRef = PropertyRef("disk_size_gb")
    caching: PropertyRef = PropertyRef("caching")
    createoption: PropertyRef = PropertyRef("create_option")
    write_accelerator_enabled: PropertyRef = PropertyRef("write_accelerator_enabled")
    managed_disk_storage_type: PropertyRef = PropertyRef(
        "managed_disk.storage_account_type"
    )


@dataclass(frozen=True)
class AzureDataDiskToVirtualMachineProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureVirtualMachine)-[:ATTACHED_TO]->(:AzureDataDisk)
class AzureDataDiskToVirtualMachineRel(CartographyRelSchema):
    target_node_label: str = "AzureVirtualMachine"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("vm_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "ATTACHED_TO"
    properties: AzureDataDiskToVirtualMachineProperties = (
        AzureDataDiskToVirtualMachineProperties()
    )


@dataclass(frozen=True)
class AzureDataDiskToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureSubscription)-[:RESOURCE]->(:AzureDataDisk)
class AzureDataDiskToSubscriptionRel(CartographyRelSchema):
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
