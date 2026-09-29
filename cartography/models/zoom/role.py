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
class ZoomRoleProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Account-scoped Zoom role ID.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    account_id: PropertyRef = PropertyRef(
        "ACCOUNT_ID",
        set_in_kwargs=True,
        extra_index=True,
        description="Owning Zoom account ID.",
    )
    zoom_id: PropertyRef = PropertyRef(
        "zoom_id", description="Role id from the Roles API.", extra_index=False
    )
    name: PropertyRef = PropertyRef("name", description="Role name.", extra_index=True)
    description: PropertyRef = PropertyRef(
        "description", description="Role description.", extra_index=False
    )
    total_members: PropertyRef = PropertyRef(
        "total_members",
        description="Provider total_members; only primary membership is correlated from the user inventory.",
        extra_index=False,
    )


@dataclass(frozen=True)
class ZoomRoleMemberRel(CartographyRelSchema):
    """HAS_ROLE relationship to ZoomUser."""

    target_node_label: str = "ZoomUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("member_ids", one_to_many=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_ROLE"
    properties: ZoomResourceRelProperties = ZoomResourceRelProperties()


@dataclass(frozen=True)
class ZoomRoleSchema(CartographyNodeSchema):
    """A common account role and its assigned primary users; privileges are separate nodes."""

    label: str = "ZoomRole"
    properties: ZoomRoleProperties = ZoomRoleProperties()
    sub_resource_relationship: ZoomAccountResourceRel = ZoomAccountResourceRel()
    other_relationships: OtherRelationships = OtherRelationships([ZoomRoleMemberRel()])
