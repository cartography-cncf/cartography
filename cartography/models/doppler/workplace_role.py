from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class DopplerWorkplaceRoleNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("identifier")
    name: PropertyRef = PropertyRef("name")
    permissions: PropertyRef = PropertyRef("permissions")
    is_custom_role: PropertyRef = PropertyRef("is_custom_role")
    is_inline_role: PropertyRef = PropertyRef("is_inline_role")
    created_at: PropertyRef = PropertyRef("created_at")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DopplerWorkplaceRoleToWorkplaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DopplerWorkplace)-[:RESOURCE]->(:DopplerWorkplaceRole)
class DopplerWorkplaceRoleToWorkplaceRel(CartographyRelSchema):
    target_node_label: str = "DopplerWorkplace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKPLACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DopplerWorkplaceRoleToWorkplaceRelProperties = (
        DopplerWorkplaceRoleToWorkplaceRelProperties()
    )


@dataclass(frozen=True)
class DopplerWorkplaceRoleSchema(CartographyNodeSchema):
    label: str = "DopplerWorkplaceRole"
    properties: DopplerWorkplaceRoleNodeProperties = (
        DopplerWorkplaceRoleNodeProperties()
    )
    sub_resource_relationship: DopplerWorkplaceRoleToWorkplaceRel = (
        DopplerWorkplaceRoleToWorkplaceRel()
    )
