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
class IntuneManagedDeviceNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    device_name: PropertyRef = PropertyRef("device_name", extra_index=True)
    user_id: PropertyRef = PropertyRef("user_id")
    user_principal_name: PropertyRef = PropertyRef("user_principal_name")
    managed_device_owner_type: PropertyRef = PropertyRef("managed_device_owner_type")
    operating_system: PropertyRef = PropertyRef("operating_system")
    os_version: PropertyRef = PropertyRef("os_version")
    compliance_state: PropertyRef = PropertyRef("compliance_state")
    is_encrypted: PropertyRef = PropertyRef("is_encrypted")
    jail_broken: PropertyRef = PropertyRef("jail_broken")
    management_agent: PropertyRef = PropertyRef("management_agent")
    manufacturer: PropertyRef = PropertyRef("manufacturer")
    model: PropertyRef = PropertyRef("model")
    serial_number: PropertyRef = PropertyRef("serial_number", extra_index=True)
    imei: PropertyRef = PropertyRef("imei")
    meid: PropertyRef = PropertyRef("meid")
    wifi_mac_address: PropertyRef = PropertyRef("wifi_mac_address")
    ethernet_mac_address: PropertyRef = PropertyRef("ethernet_mac_address")
    azure_ad_device_id: PropertyRef = PropertyRef("azure_ad_device_id")
    azure_ad_registered: PropertyRef = PropertyRef("azure_ad_registered")
    device_enrollment_type: PropertyRef = PropertyRef("device_enrollment_type")
    device_registration_state: PropertyRef = PropertyRef("device_registration_state")
    is_supervised: PropertyRef = PropertyRef("is_supervised")
    enrolled_date_time: PropertyRef = PropertyRef("enrolled_date_time")
    last_sync_date_time: PropertyRef = PropertyRef("last_sync_date_time")
    eas_activated: PropertyRef = PropertyRef("eas_activated")
    eas_device_id: PropertyRef = PropertyRef("eas_device_id")
    partner_reported_threat_state: PropertyRef = PropertyRef(
        "partner_reported_threat_state",
    )
    total_storage_space_in_bytes: PropertyRef = PropertyRef(
        "total_storage_space_in_bytes",
    )
    free_storage_space_in_bytes: PropertyRef = PropertyRef(
        "free_storage_space_in_bytes",
    )
    physical_memory_in_bytes: PropertyRef = PropertyRef("physical_memory_in_bytes")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class IntuneManagedDeviceToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:IntuneManagedDevice)<-[:RESOURCE]-(:EntraTenant)
@dataclass(frozen=True)
class IntuneManagedDeviceToTenantRel(CartographyRelSchema):
    target_node_label: str = "EntraTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TENANT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: IntuneManagedDeviceToTenantRelProperties = (
        IntuneManagedDeviceToTenantRelProperties()
    )


# (:EntraUser)-[:ENROLLED_TO]->(:IntuneManagedDevice)
@dataclass(frozen=True)
class IntuneManagedDeviceToEntraUserRel(CartographyRelSchema):
    target_node_label: str = "EntraUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("user_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "ENROLLED_TO"
    properties: IntuneManagedDeviceToTenantRelProperties = (
        IntuneManagedDeviceToTenantRelProperties()
    )


@dataclass(frozen=True)
class IntuneManagedDeviceSchema(CartographyNodeSchema):
    label: str = "IntuneManagedDevice"
    properties: IntuneManagedDeviceNodeProperties = IntuneManagedDeviceNodeProperties()
    sub_resource_relationship: IntuneManagedDeviceToTenantRel = (
        IntuneManagedDeviceToTenantRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            IntuneManagedDeviceToEntraUserRel(),
        ],
    )
