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
class JamfComputerNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Jamf computer inventory ID.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )
    udid: PropertyRef = PropertyRef("udid", description="Device UDID.")
    name: PropertyRef = PropertyRef(
        "name",
        extra_index=True,
        description="Device hostname.",
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
    platform: PropertyRef = PropertyRef(
        "platform",
        description="Platform reported by Jamf.",
    )
    os_name: PropertyRef = PropertyRef(
        "os_name", description="Operating system family."
    )
    os_version: PropertyRef = PropertyRef(
        "os_version",
        description="Operating system version.",
    )
    os_build: PropertyRef = PropertyRef(
        "os_build",
        description="Operating system build.",
    )
    report_date: PropertyRef = PropertyRef(
        "report_date",
        description="Last inventory report timestamp.",
    )
    last_contact_time: PropertyRef = PropertyRef(
        "last_contact_time",
        description="Last Jamf contact timestamp.",
    )
    site_name: PropertyRef = PropertyRef("site_name", description="Jamf site name.")
    supervised: PropertyRef = PropertyRef(
        "supervised",
        description="Whether the device is supervised.",
    )
    user_approved_mdm: PropertyRef = PropertyRef(
        "user_approved_mdm",
        description="Whether mobile device management is user approved.",
    )
    declarative_device_management_enabled: PropertyRef = PropertyRef(
        "declarative_device_management_enabled",
        description="Whether declarative device management is enabled.",
    )
    enrolled_via_automated_device_enrollment: PropertyRef = PropertyRef(
        "enrolled_via_automated_device_enrollment",
        description="Whether automated device enrollment was used.",
    )
    remote_management_managed: PropertyRef = PropertyRef(
        "remote_management_managed",
        description="Whether remote management is enabled.",
    )
    filevault_enabled: PropertyRef = PropertyRef(
        "filevault_enabled",
        description="Whether FileVault is enabled.",
    )
    firewall_enabled: PropertyRef = PropertyRef(
        "firewall_enabled",
        description="Whether the firewall is enabled.",
    )
    gatekeeper_status: PropertyRef = PropertyRef(
        "gatekeeper_status",
        description="Gatekeeper status.",
    )
    sip_status: PropertyRef = PropertyRef(
        "sip_status",
        description="System Integrity Protection status.",
    )
    secure_boot_level: PropertyRef = PropertyRef(
        "secure_boot_level",
        description="Secure Boot level.",
    )
    activation_lock_enabled: PropertyRef = PropertyRef(
        "activation_lock_enabled",
        description="Whether Activation Lock is enabled.",
    )
    recovery_lock_enabled: PropertyRef = PropertyRef(
        "recovery_lock_enabled",
        description="Whether Recovery Lock is enabled.",
    )
    bootstrap_token_escrowed_status: PropertyRef = PropertyRef(
        "bootstrap_token_escrowed_status",
        description="Bootstrap token escrow state.",
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
class JamfComputerToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class JamfComputerToTenantRel(CartographyRelSchema):
    """Links a Jamf tenant to one of its managed computers."""

    target_node_label: str = "JamfTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TENANT_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: JamfComputerToTenantRelProperties = JamfComputerToTenantRelProperties()


@dataclass(frozen=True)
class JamfComputerToGroupRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class JamfComputerToGroupRel(CartographyRelSchema):
    """Links a Jamf computer to a group containing it."""

    target_node_label: str = "JamfComputerGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("group_ids", one_to_many=True)}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF"
    properties: JamfComputerToGroupRelProperties = JamfComputerToGroupRelProperties()


@dataclass(frozen=True)
class JamfComputerSchema(CartographyNodeSchema):
    """A macOS computer inventory record managed by Jamf."""

    label: str = "JamfComputer"
    properties: JamfComputerNodeProperties = JamfComputerNodeProperties()
    sub_resource_relationship: JamfComputerToTenantRel = JamfComputerToTenantRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [JamfComputerToGroupRel()]
    )
