from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.zoom.resource import ZoomAccountResourceRel
from cartography.models.zoom.resource import ZoomResourceRelProperties


@dataclass(frozen=True)
class ZoomRolePrivilegeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Account-scoped role ID and privilege identifier."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    account_id: PropertyRef = PropertyRef(
        "ACCOUNT_ID",
        set_in_kwargs=True,
        extra_index=True,
        description="Owning Zoom account ID.",
    )
    privilege: PropertyRef = PropertyRef(
        "privilege", description="Role privileges entry.", extra_index=True
    )
    restricted_to_groups: PropertyRef = PropertyRef(
        "restricted_to_groups",
        description="True when privilege_scopes restricts this privilege to group_ids; false indicates no group restriction returned.",
    )
    group_ids: PropertyRef = PropertyRef(
        "group_ids",
        description="Provider group IDs from privilege_scopes; empty when no group restriction is returned.",
        extra_index=False,
    )


@dataclass(frozen=True)
class ZoomRoleGrantsRel(CartographyRelSchema):
    """GRANTS relationship to ZoomRole."""

    target_node_label: str = "ZoomRole"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("role_node_id", one_to_many=False)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "GRANTS"
    properties: ZoomResourceRelProperties = ZoomResourceRelProperties()


@dataclass(frozen=True)
class ZoomPrivilegeScopeRel(CartographyRelSchema):
    """SCOPED_TO relationship to ZoomGroup."""

    target_node_label: str = "ZoomGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("group_node_ids", one_to_many=True)}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "SCOPED_TO"
    properties: ZoomResourceRelProperties = ZoomResourceRelProperties()


@dataclass(frozen=True)
class ZoomRolePrivilegeSchema(CartographyNodeSchema):
    """One privilege granted by a role, with explicit group restrictions when returned."""

    label: str = "ZoomRolePrivilege"
    properties: ZoomRolePrivilegeProperties = ZoomRolePrivilegeProperties()
    sub_resource_relationship: ZoomAccountResourceRel = ZoomAccountResourceRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [ZoomRoleGrantsRel(), ZoomPrivilegeScopeRel()]
    )
