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
class AzureVirtualMachineProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")
    location: PropertyRef = PropertyRef("location")
    resourcegroup: PropertyRef = PropertyRef("resource_group")
    type: PropertyRef = PropertyRef("type")
    plan: PropertyRef = PropertyRef("plan.product")
    size: PropertyRef = PropertyRef("hardware_profile.vm_size")
    license_type: PropertyRef = PropertyRef("license_type")
    computer_name: PropertyRef = PropertyRef("os_profile.computer_name")
    identity_type: PropertyRef = PropertyRef("identity.type")
    zones: PropertyRef = PropertyRef("zones")
    ultra_ssd_enabled: PropertyRef = PropertyRef(
        "additional_capabilities.ultra_ssd_enabled"
    )
    priority: PropertyRef = PropertyRef("priority")
    eviction_policy: PropertyRef = PropertyRef("eviction_policy")


@dataclass(frozen=True)
class AzureVirtualMachineToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureSubscription)-[:RESOURCE]->(:AzureVirtualMachine)
class AzureVirtualMachineToSubscriptionRel(CartographyRelSchema):
    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureVirtualMachineToSubscriptionRelProperties = (
        AzureVirtualMachineToSubscriptionRelProperties()
    )


@dataclass(frozen=True)
class AzureVirtualMachineSchema(CartographyNodeSchema):
    label: str = "AzureVirtualMachine"
    properties: AzureVirtualMachineProperties = AzureVirtualMachineProperties()
    sub_resource_relationship: AzureVirtualMachineToSubscriptionRel = (
        AzureVirtualMachineToSubscriptionRel()
    )
