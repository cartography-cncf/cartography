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
    id: PropertyRef = PropertyRef("id", description="Intune managed device ID.")
    device_name: PropertyRef = PropertyRef(
        "device_name", extra_index=True, description="Name of the managed device."
    )
    user_id: PropertyRef = PropertyRef(
        "user_id", description="Entra user ID associated with the device."
    )
    user_principal_name: PropertyRef = PropertyRef(
        "user_principal_name",
        description="User principal name associated with the device.",
    )
    managed_device_owner_type: PropertyRef = PropertyRef(
        "managed_device_owner_type", description="Ownership type of the managed device."
    )
    operating_system: PropertyRef = PropertyRef(
        "operating_system", description="Operating system of the device."
    )
    os_version: PropertyRef = PropertyRef(
        "os_version", description="Operating system version of the device."
    )
    compliance_state: PropertyRef = PropertyRef(
        "compliance_state", description="Intune compliance state of the device."
    )
    is_encrypted: PropertyRef = PropertyRef(
        "is_encrypted", description="Whether the device storage is encrypted."
    )
    jail_broken: PropertyRef = PropertyRef(
        "jail_broken", description="Whether the device is jailbroken or rooted."
    )
    management_agent: PropertyRef = PropertyRef(
        "management_agent", description="Management channel used by the device."
    )
    manufacturer: PropertyRef = PropertyRef(
        "manufacturer", description="Manufacturer of the device."
    )
    model: PropertyRef = PropertyRef("model", description="Model of the device.")
    serial_number: PropertyRef = PropertyRef(
        "serial_number", extra_index=True, description="Serial number of the device."
    )
    imei: PropertyRef = PropertyRef(
        "imei", description="International Mobile Equipment Identity of the device."
    )
    meid: PropertyRef = PropertyRef(
        "meid", description="Mobile Equipment Identifier of the device."
    )
    wifi_mac_address: PropertyRef = PropertyRef(
        "wifi_mac_address", description="Wi-Fi MAC address of the device."
    )
    ethernet_mac_address: PropertyRef = PropertyRef(
        "ethernet_mac_address", description="Ethernet MAC address of the device."
    )
    azure_ad_device_id: PropertyRef = PropertyRef(
        "azure_ad_device_id", description="Microsoft Entra device ID."
    )
    azure_ad_registered: PropertyRef = PropertyRef(
        "azure_ad_registered",
        description="Whether the device is registered in Entra ID.",
    )
    device_enrollment_type: PropertyRef = PropertyRef(
        "device_enrollment_type", description="Method used to enroll the device."
    )
    device_registration_state: PropertyRef = PropertyRef(
        "device_registration_state", description="Registration state of the device."
    )
    is_supervised: PropertyRef = PropertyRef(
        "is_supervised", description="Whether the device is supervised."
    )
    enrolled_date_time: PropertyRef = PropertyRef(
        "enrolled_date_time", description="Timestamp when the device was enrolled."
    )
    last_sync_date_time: PropertyRef = PropertyRef(
        "last_sync_date_time",
        description="Timestamp of the latest Intune synchronization.",
    )
    eas_activated: PropertyRef = PropertyRef(
        "eas_activated", description="Whether Exchange ActiveSync is activated."
    )
    eas_device_id: PropertyRef = PropertyRef(
        "eas_device_id", description="Exchange ActiveSync device ID."
    )
    partner_reported_threat_state: PropertyRef = PropertyRef(
        "partner_reported_threat_state",
        description="Threat state reported by a mobile threat defense partner.",
    )
    total_storage_space_in_bytes: PropertyRef = PropertyRef(
        "total_storage_space_in_bytes",
        description="Total device storage capacity in bytes.",
    )
    free_storage_space_in_bytes: PropertyRef = PropertyRef(
        "free_storage_space_in_bytes",
        description="Available device storage in bytes.",
    )
    physical_memory_in_bytes: PropertyRef = PropertyRef(
        "physical_memory_in_bytes", description="Physical memory capacity in bytes."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the latest Cartography update.",
    )


@dataclass(frozen=True)
class IntuneManagedDeviceToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:IntuneManagedDevice)<-[:RESOURCE]-(:AzureTenant)
@dataclass(frozen=True)
class IntuneManagedDeviceToTenantRel(CartographyRelSchema):
    """Links a Microsoft tenant to one of its Intune managed devices."""

    target_node_label: str = "AzureTenant"
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
    """Links an Entra user to a device they enrolled in Intune."""

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
    """A device managed by Microsoft Intune."""

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
