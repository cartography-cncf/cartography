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

    id: PropertyRef = PropertyRef("deviceId")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    hostname: PropertyRef = PropertyRef("hostname", extra_index=True)

    # Device information
    model: PropertyRef = PropertyRef("model")
    manufacturer: PropertyRef = PropertyRef("manufacturer")
    release_version: PropertyRef = PropertyRef("releaseVersion")
    brand: PropertyRef = PropertyRef("brand")
    build_number: PropertyRef = PropertyRef("buildNumber")
    kernel_version: PropertyRef = PropertyRef("kernelVersion")
    baseband_version: PropertyRef = PropertyRef("basebandVersion")
    device_type: PropertyRef = PropertyRef("deviceType")
    os_version: PropertyRef = PropertyRef("osVersion")
    owner_type: PropertyRef = PropertyRef("ownerType")
    serial_number: PropertyRef = PropertyRef("serialNumber")
    asset_tag: PropertyRef = PropertyRef("assetTag")
    imei: PropertyRef = PropertyRef("imei")
    meid: PropertyRef = PropertyRef("meid")
    wifi_mac_addresses: PropertyRef = PropertyRef("wifiMacAddresses")
    network_operator: PropertyRef = PropertyRef("networkOperator")

    # Security and state
    encryption_state: PropertyRef = PropertyRef("encryptionState")
    compromised_state: PropertyRef = PropertyRef("compromisedState")
    management_state: PropertyRef = PropertyRef("managementState")

    # Timestamps
    create_time: PropertyRef = PropertyRef("createTime")
    last_sync_time: PropertyRef = PropertyRef("lastSyncTime")
    security_patch_time: PropertyRef = PropertyRef("securityPatchTime")

    # Android specific
    android_specific_attributes: PropertyRef = PropertyRef("androidSpecificAttributes")
    enabled_developer_options: PropertyRef = PropertyRef("enabledDeveloperOptions")
    enabled_usb_debugging: PropertyRef = PropertyRef("enabledUsbDebugging")
    bootloader_version: PropertyRef = PropertyRef("bootloaderVersion")
    other_accounts: PropertyRef = PropertyRef("otherAccounts")

    # Additional identifiers
    unified_device_id: PropertyRef = PropertyRef("unifiedDeviceId")
    endpoint_verification_specific_attributes: PropertyRef = PropertyRef(
        "endpointVerificationSpecificAttributes"
    )

    # Tenant relationship
    customer_id: PropertyRef = PropertyRef("CUSTOMER_ID", set_in_kwargs=True)


@dataclass(frozen=True)
class GoogleWorkspaceDeviceToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GoogleWorkspaceDeviceToTenantRel(CartographyRelSchema):
    """
    Relationship from Google Workspace device to Google Workspace tenant
    """

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
    """
    Google Workspace device node schema
    """

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
