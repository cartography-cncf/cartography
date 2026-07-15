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
class JumpCloudSystemNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="JumpCloud asset ID.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last update.",
    )
    jc_system_id: PropertyRef = PropertyRef(
        "jcSystemId",
        extra_index=True,
        description="JumpCloud system ID used to correlate system insights data.",
    )
    primary_user: PropertyRef = PropertyRef(
        "primary_user",
        description="Display name of the primary user assigned to the device.",
    )
    primary_user_id: PropertyRef = PropertyRef(
        "primary_user_id",
        description="JumpCloud ID of the primary user.",
    )
    model: PropertyRef = PropertyRef("model", description="Device hardware model.")
    os_family: PropertyRef = PropertyRef(
        "os_family",
        description="Operating system family.",
    )
    os_version: PropertyRef = PropertyRef(
        "os_version",
        description="Operating system version.",
    )
    os: PropertyRef = PropertyRef(
        "os",
        description="Full operating system name.",
    )
    status: PropertyRef = PropertyRef("status", description="Device status.")
    serial_number: PropertyRef = PropertyRef(
        "serial_number",
        description="Device serial number.",
    )


@dataclass(frozen=True)
class JumpCloudSystemToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class JumpCloudSystemToTenantRel(CartographyRelSchema):
    """The tenant contains the managed system."""

    target_node_label: str = "JumpCloudTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: JumpCloudSystemToTenantRelProperties = (
        JumpCloudSystemToTenantRelProperties()
    )


@dataclass(frozen=True)
class JumpCloudSystemToUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class JumpCloudSystemToUserRel(CartographyRelSchema):
    """A user owns the managed system."""

    target_node_label: str = "JumpCloudUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("primary_user_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "OWNS"
    properties: JumpCloudSystemToUserRelProperties = (
        JumpCloudSystemToUserRelProperties()
    )


@dataclass(frozen=True)
class JumpCloudSystemSchema(CartographyNodeSchema):
    """A managed device in JumpCloud."""

    label: str = "JumpCloudSystem"
    properties: JumpCloudSystemNodeProperties = JumpCloudSystemNodeProperties()
    sub_resource_relationship: JumpCloudSystemToTenantRel = JumpCloudSystemToTenantRel()
    other_relationships: OtherRelationships = OtherRelationships(
        rels=[JumpCloudSystemToUserRel()],
    )
