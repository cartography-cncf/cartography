from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_source_node_matcher
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import SourceNodeMatcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class OktaDeviceNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Unique Okta device identifier.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    status: PropertyRef = PropertyRef("status", description="Device lifecycle status.")
    created: PropertyRef = PropertyRef("created", description="Device creation time.")
    okta_last_updated: PropertyRef = PropertyRef(
        "okta_last_updated",
        description="Time when Okta last updated the device.",
    )
    display_name: PropertyRef = PropertyRef(
        "display_name",
        extra_index=True,
        description="User-facing device name.",
    )
    platform: PropertyRef = PropertyRef(
        "platform",
        description="Device platform reported by Okta.",
    )
    serial_number: PropertyRef = PropertyRef(
        "serial_number",
        extra_index=True,
        description="Device serial number.",
    )
    sid: PropertyRef = PropertyRef("sid", description="Windows security identifier.")
    manufacturer: PropertyRef = PropertyRef(
        "manufacturer",
        description="Device manufacturer.",
    )
    model: PropertyRef = PropertyRef("model", description="Device model.")
    os_version: PropertyRef = PropertyRef(
        "os_version",
        description="Device operating system version.",
    )
    registered: PropertyRef = PropertyRef(
        "registered",
        description="Whether the device is registered in Okta.",
    )
    managed: PropertyRef = PropertyRef(
        "managed",
        description="Whether the device is managed by MDM software.",
    )
    secure_hardware_present: PropertyRef = PropertyRef(
        "secure_hardware_present",
        description="Whether secure hardware is present.",
    )
    disk_encryption_type: PropertyRef = PropertyRef(
        "disk_encryption_type",
        description="Device disk encryption type.",
    )
    integrity_jailbreak: PropertyRef = PropertyRef(
        "integrity_jailbreak",
        description="Whether the device is jailbroken or rooted.",
    )
    imei: PropertyRef = PropertyRef("imei", description="Device IMEI.")
    meid: PropertyRef = PropertyRef("meid", description="Device MEID.")
    udid: PropertyRef = PropertyRef("udid", description="Device UDID.")
    tpm_public_key_hash: PropertyRef = PropertyRef(
        "tpm_public_key_hash",
        description="Windows TPM public key hash.",
    )
    resource_type: PropertyRef = PropertyRef(
        "resource_type",
        description="Okta resource type.",
    )
    resource_display_name: PropertyRef = PropertyRef(
        "resource_display_name",
        description="Display name from the Okta resource metadata.",
    )
    resource_display_name_sensitive: PropertyRef = PropertyRef(
        "resource_display_name_sensitive",
        description="Whether the resource display name contains sensitive data.",
    )
    resource_alternate_id: PropertyRef = PropertyRef(
        "resource_alternate_id",
        description="Alternate identifier for the Okta resource.",
    )


@dataclass(frozen=True)
class OktaDeviceToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class OktaDeviceToOrganizationRel(CartographyRelSchema):
    """An Okta organization contains a registered device."""

    target_node_label: str = "OktaOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("OKTA_ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: OktaDeviceToOrganizationRelProperties = (
        OktaDeviceToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class OktaUserOwnsDeviceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label",
        set_in_kwargs=True,
    )
    _sub_resource_id: PropertyRef = PropertyRef(
        "_sub_resource_id",
        set_in_kwargs=True,
    )
    management_status: PropertyRef = PropertyRef(
        "management_status",
        description="Device management status for this user enrollment.",
    )
    screen_lock_type: PropertyRef = PropertyRef(
        "screen_lock_type",
        description="Screen lock type reported for this user enrollment.",
    )
    enrolled_at: PropertyRef = PropertyRef(
        "enrolled_at",
        description="Time when the user enrolled the device.",
    )


@dataclass(frozen=True)
class OktaUserOwnsDeviceRel(CartographyRelSchema):
    """An Okta user owns a registered device."""

    source_node_label: str = "OktaUser"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("user_id")},
    )
    target_node_label: str = "OktaDevice"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("device_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "OWNS"
    properties: OktaUserOwnsDeviceRelProperties = OktaUserOwnsDeviceRelProperties()


@dataclass(frozen=True)
class OktaDeviceSchema(CartographyNodeSchema):
    """A device registered or managed in Okta."""

    label: str = "OktaDevice"
    properties: OktaDeviceNodeProperties = OktaDeviceNodeProperties()
    sub_resource_relationship: OktaDeviceToOrganizationRel = (
        OktaDeviceToOrganizationRel()
    )
