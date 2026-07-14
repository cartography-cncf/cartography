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
class GoogleWorkspaceDeviceNodeProperties(CartographyNodeProperties):
    """
    Google Workspace device node properties
    """

    id: PropertyRef = PropertyRef(
        "deviceId", description="Unique Google Workspace device ID."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last update.",
    )
    hostname: PropertyRef = PropertyRef(
        "hostname", extra_index=True, description="Hostname of the device."
    )

    # Device information
    model: PropertyRef = PropertyRef("model", description="Model of the device.")
    manufacturer: PropertyRef = PropertyRef(
        "manufacturer", description="Manufacturer of the device."
    )
    release_version: PropertyRef = PropertyRef(
        "releaseVersion", description="Release version reported by the device."
    )
    brand: PropertyRef = PropertyRef("brand", description="Brand of the device.")
    build_number: PropertyRef = PropertyRef(
        "buildNumber", description="Operating system build number."
    )
    kernel_version: PropertyRef = PropertyRef(
        "kernelVersion", description="Operating system kernel version."
    )
    baseband_version: PropertyRef = PropertyRef(
        "basebandVersion", description="Mobile baseband version."
    )
    device_type: PropertyRef = PropertyRef(
        "deviceType", description="Type of the device."
    )
    os_version: PropertyRef = PropertyRef(
        "osVersion", description="Operating system version."
    )
    owner_type: PropertyRef = PropertyRef(
        "ownerType", description="Ownership classification of the device."
    )
    serial_number: PropertyRef = PropertyRef(
        "serialNumber", description="Serial number of the device."
    )
    asset_tag: PropertyRef = PropertyRef(
        "assetTag", description="Asset tag assigned to the device."
    )
    imei: PropertyRef = PropertyRef(
        "imei", description="International Mobile Equipment Identity."
    )
    meid: PropertyRef = PropertyRef("meid", description="Mobile Equipment Identifier.")
    wifi_mac_addresses: PropertyRef = PropertyRef(
        "wifiMacAddresses", description="Wi-Fi MAC addresses of the device."
    )
    network_operator: PropertyRef = PropertyRef(
        "networkOperator", description="Mobile network operator."
    )

    # Security and state
    encryption_state: PropertyRef = PropertyRef(
        "encryptionState", description="Encryption state of the device."
    )
    compromised_state: PropertyRef = PropertyRef(
        "compromisedState", description="Security compromise state of the device."
    )
    management_state: PropertyRef = PropertyRef(
        "managementState", description="Management state of the device."
    )

    # Timestamps
    create_time: PropertyRef = PropertyRef(
        "createTime", description="Time when the device record was created."
    )
    last_sync_time: PropertyRef = PropertyRef(
        "lastSyncTime", description="Time when the device last synchronized."
    )
    security_patch_time: PropertyRef = PropertyRef(
        "securityPatchTime", description="Time of the installed security patch."
    )

    # Android specific
    android_specific_attributes: PropertyRef = PropertyRef(
        "androidSpecificAttributes",
        description="Android-specific attributes reported for the device.",
    )
    enabled_developer_options: PropertyRef = PropertyRef(
        "enabledDeveloperOptions",
        description="Whether Android developer options are enabled.",
    )
    enabled_usb_debugging: PropertyRef = PropertyRef(
        "enabledUsbDebugging",
        description="Whether Android USB debugging is enabled.",
    )
    bootloader_version: PropertyRef = PropertyRef(
        "bootloaderVersion", description="Android bootloader version."
    )
    other_accounts: PropertyRef = PropertyRef(
        "otherAccounts", description="Other accounts present on the device."
    )

    # Additional identifiers
    unified_device_id: PropertyRef = PropertyRef(
        "unifiedDeviceId", description="Unified identifier for the device."
    )
    endpoint_verification_specific_attributes: PropertyRef = PropertyRef(
        "endpointVerificationSpecificAttributes",
        description="Endpoint Verification attributes reported for the device.",
    )

    # Tenant relationship
    customer_id: PropertyRef = PropertyRef(
        "CUSTOMER_ID",
        set_in_kwargs=True,
        description="ID of the Google Workspace tenant that contains the device.",
    )


@dataclass(frozen=True)
class GoogleWorkspaceDeviceToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GoogleWorkspaceDeviceToTenantRel(CartographyRelSchema):
    """A Google Workspace tenant contains a managed device."""

    target_node_label: str = "GoogleWorkspaceTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("CUSTOMER_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GoogleWorkspaceDeviceToTenantRelProperties = (
        GoogleWorkspaceDeviceToTenantRelProperties()
    )


# Direct relationship from GoogleWorkspaceUser to GoogleWorkspaceDevice
@dataclass(frozen=True)
class GoogleWorkspaceUserToDeviceRelProperties(CartographyRelProperties):
    # Required for all MatchLinks
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GoogleWorkspaceUserToDeviceRel(CartographyRelSchema):
    """A Google Workspace user directly owns a managed device."""

    target_node_label: str = "GoogleWorkspaceUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "primary_email": PropertyRef("owner_email"),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "OWNS"
    properties: GoogleWorkspaceUserToDeviceRelProperties = (
        GoogleWorkspaceUserToDeviceRelProperties()
    )


@dataclass(frozen=True)
class GoogleWorkspaceDeviceSchema(CartographyNodeSchema):
    """A device managed by Google Workspace."""

    label: str = "GoogleWorkspaceDevice"
    properties: GoogleWorkspaceDeviceNodeProperties = (
        GoogleWorkspaceDeviceNodeProperties()
    )
    sub_resource_relationship: GoogleWorkspaceDeviceToTenantRel = (
        GoogleWorkspaceDeviceToTenantRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GoogleWorkspaceUserToDeviceRel(),
        ]
    )
