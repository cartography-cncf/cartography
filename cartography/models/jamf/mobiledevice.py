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
class JamfMobileDeviceNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Jamf mobile device inventory ID.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )
    display_name: PropertyRef = PropertyRef(
        "display_name",
        extra_index=True,
        description="Device display name.",
    )
    managed: PropertyRef = PropertyRef(
        "managed",
        description="Whether the device is managed.",
    )
    supervised: PropertyRef = PropertyRef(
        "supervised",
        description="Whether the device is supervised.",
    )
    last_inventory_update_date: PropertyRef = PropertyRef(
        "last_inventory_update_date",
        description="Last inventory update timestamp.",
    )
    last_enrolled_date: PropertyRef = PropertyRef(
        "last_enrolled_date",
        description="Enrollment timestamp.",
    )
    platform: PropertyRef = PropertyRef(
        "platform",
        description="Device type reported by Jamf.",
    )
    os: PropertyRef = PropertyRef(
        "os",
        description="Normalized operating system family.",
    )
    os_version: PropertyRef = PropertyRef(
        "os_version",
        description="Operating system version.",
    )
    os_build: PropertyRef = PropertyRef(
        "os_build",
        description="Operating system build.",
    )
    serial_number: PropertyRef = PropertyRef(
        "serial_number",
        extra_index=True,
        description="Device serial number.",
    )
    model: PropertyRef = PropertyRef("model", description="Device model.")
    model_identifier: PropertyRef = PropertyRef(
        "model_identifier",
        description="Device model identifier.",
    )
    activation_lock_enabled: PropertyRef = PropertyRef(
        "activation_lock_enabled",
        description="Whether Activation Lock is enabled.",
    )
    bootstrap_token_escrowed: PropertyRef = PropertyRef(
        "bootstrap_token_escrowed",
        description="Whether a bootstrap token is escrowed.",
    )
    data_protected: PropertyRef = PropertyRef(
        "data_protected",
        description="Whether data protection is enabled.",
    )
    hardware_encryption: PropertyRef = PropertyRef(
        "hardware_encryption",
        description="Whether hardware encryption is enabled.",
    )
    jailbreak_detected: PropertyRef = PropertyRef(
        "jailbreak_detected",
        description="Whether jailbreaking or rooting was detected.",
    )
    lost_mode_enabled: PropertyRef = PropertyRef(
        "lost_mode_enabled",
        description="Whether lost mode is enabled.",
    )
    passcode_compliant: PropertyRef = PropertyRef(
        "passcode_compliant",
        description="Whether the passcode meets policy.",
    )
    passcode_present: PropertyRef = PropertyRef(
        "passcode_present",
        description="Whether a passcode is present.",
    )
    username: PropertyRef = PropertyRef(
        "username",
        description="Associated username.",
    )
    user_real_name: PropertyRef = PropertyRef(
        "user_real_name",
        description="Associated user's real name.",
    )
    email: PropertyRef = PropertyRef(
        "email",
        description="Associated email address.",
    )


@dataclass(frozen=True)
class JamfMobileDeviceToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class JamfMobileDeviceToTenantRel(CartographyRelSchema):
    """Links a Jamf tenant to one of its managed mobile devices."""

    target_node_label: str = "JamfTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TENANT_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: JamfMobileDeviceToTenantRelProperties = (
        JamfMobileDeviceToTenantRelProperties()
    )


@dataclass(frozen=True)
class JamfMobileDeviceToGroupRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class JamfMobileDeviceToGroupRel(CartographyRelSchema):
    """Links a Jamf mobile device to a group containing it."""

    target_node_label: str = "JamfMobileDeviceGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("group_ids", one_to_many=True)}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF"
    properties: JamfMobileDeviceToGroupRelProperties = (
        JamfMobileDeviceToGroupRelProperties()
    )


@dataclass(frozen=True)
class JamfMobileDeviceSchema(CartographyNodeSchema):
    """A mobile device inventory record managed by Jamf."""

    label: str = "JamfMobileDevice"
    properties: JamfMobileDeviceNodeProperties = JamfMobileDeviceNodeProperties()
    sub_resource_relationship: JamfMobileDeviceToTenantRel = (
        JamfMobileDeviceToTenantRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [JamfMobileDeviceToGroupRel()]
    )
