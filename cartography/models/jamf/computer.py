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
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    udid: PropertyRef = PropertyRef("udid")
    name: PropertyRef = PropertyRef("name", extra_index=True)
    serial_number: PropertyRef = PropertyRef("serial_number", extra_index=True)
    model: PropertyRef = PropertyRef("model")
    model_identifier: PropertyRef = PropertyRef("model_identifier")
    platform: PropertyRef = PropertyRef("platform")
    os_name: PropertyRef = PropertyRef("os_name")
    os_version: PropertyRef = PropertyRef("os_version")
    os_build: PropertyRef = PropertyRef("os_build")
    report_date: PropertyRef = PropertyRef("report_date")
    last_contact_time: PropertyRef = PropertyRef("last_contact_time")
    site_name: PropertyRef = PropertyRef("site_name")
    supervised: PropertyRef = PropertyRef("supervised")
    user_approved_mdm: PropertyRef = PropertyRef("user_approved_mdm")
    declarative_device_management_enabled: PropertyRef = PropertyRef(
        "declarative_device_management_enabled"
    )
    enrolled_via_automated_device_enrollment: PropertyRef = PropertyRef(
        "enrolled_via_automated_device_enrollment"
    )
    remote_management_managed: PropertyRef = PropertyRef("remote_management_managed")
    filevault_enabled: PropertyRef = PropertyRef("filevault_enabled")
    firewall_enabled: PropertyRef = PropertyRef("firewall_enabled")
    gatekeeper_status: PropertyRef = PropertyRef("gatekeeper_status")
    sip_status: PropertyRef = PropertyRef("sip_status")
    secure_boot_level: PropertyRef = PropertyRef("secure_boot_level")
    activation_lock_enabled: PropertyRef = PropertyRef("activation_lock_enabled")
    recovery_lock_enabled: PropertyRef = PropertyRef("recovery_lock_enabled")
    bootstrap_token_escrowed_status: PropertyRef = PropertyRef(
        "bootstrap_token_escrowed_status"
    )
    username: PropertyRef = PropertyRef("username")
    user_real_name: PropertyRef = PropertyRef("user_real_name")
    email: PropertyRef = PropertyRef("email")


@dataclass(frozen=True)
class JamfComputerToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class JamfComputerToTenantRel(CartographyRelSchema):
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
    target_node_label: str = "JamfComputerGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("group_ids", one_to_many=True)}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF"
    properties: JamfComputerToGroupRelProperties = JamfComputerToGroupRelProperties()


@dataclass(frozen=True)
class JamfComputerSchema(CartographyNodeSchema):
    label: str = "JamfComputer"
    properties: JamfComputerNodeProperties = JamfComputerNodeProperties()
    sub_resource_relationship: JamfComputerToTenantRel = JamfComputerToTenantRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [JamfComputerToGroupRel()]
    )
