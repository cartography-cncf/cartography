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
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    jc_system_id: PropertyRef = PropertyRef("jcSystemId", extra_index=True)
    primary_user: PropertyRef = PropertyRef("primary_user")
    primary_user_id: PropertyRef = PropertyRef("primary_user_id")
    model: PropertyRef = PropertyRef("model")
    os_family: PropertyRef = PropertyRef("os_family")
    os_version: PropertyRef = PropertyRef("os_version")
    os: PropertyRef = PropertyRef("os")
    status: PropertyRef = PropertyRef("status")
    serial_number: PropertyRef = PropertyRef("serial_number")


@dataclass(frozen=True)
class JumpCloudSystemToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class JumpCloudSystemToTenantRel(CartographyRelSchema):
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
    label: str = "JumpCloudSystem"
    properties: JumpCloudSystemNodeProperties = JumpCloudSystemNodeProperties()
    sub_resource_relationship: JumpCloudSystemToTenantRel = JumpCloudSystemToTenantRel()
    other_relationships: OtherRelationships = OtherRelationships(
        rels=[JumpCloudSystemToUserRel()],
    )
