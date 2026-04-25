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
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    display_name: PropertyRef = PropertyRef("display_name", extra_index=True)
    managed: PropertyRef = PropertyRef("managed")
    supervised: PropertyRef = PropertyRef("supervised")
    last_inventory_update_date: PropertyRef = PropertyRef("last_inventory_update_date")
    last_enrolled_date: PropertyRef = PropertyRef("last_enrolled_date")
    platform: PropertyRef = PropertyRef("platform")
    os: PropertyRef = PropertyRef("os")
    os_version: PropertyRef = PropertyRef("os_version")
    os_build: PropertyRef = PropertyRef("os_build")
    serial_number: PropertyRef = PropertyRef("serial_number", extra_index=True)
    model: PropertyRef = PropertyRef("model")
    model_identifier: PropertyRef = PropertyRef("model_identifier")
    activation_lock_enabled: PropertyRef = PropertyRef("activation_lock_enabled")
    bootstrap_token_escrowed: PropertyRef = PropertyRef("bootstrap_token_escrowed")
    data_protected: PropertyRef = PropertyRef("data_protected")
    hardware_encryption: PropertyRef = PropertyRef("hardware_encryption")
    jailbreak_detected: PropertyRef = PropertyRef("jailbreak_detected")
    lost_mode_enabled: PropertyRef = PropertyRef("lost_mode_enabled")
    passcode_compliant: PropertyRef = PropertyRef("passcode_compliant")
    passcode_present: PropertyRef = PropertyRef("passcode_present")
    username: PropertyRef = PropertyRef("username")
    user_real_name: PropertyRef = PropertyRef("user_real_name")
    email: PropertyRef = PropertyRef("email")


@dataclass(frozen=True)
class JamfMobileDeviceToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class JamfMobileDeviceToTenantRel(CartographyRelSchema):
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
    label: str = "JamfMobileDevice"
    properties: JamfMobileDeviceNodeProperties = JamfMobileDeviceNodeProperties()
    sub_resource_relationship: JamfMobileDeviceToTenantRel = (
        JamfMobileDeviceToTenantRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [JamfMobileDeviceToGroupRel()]
    )
