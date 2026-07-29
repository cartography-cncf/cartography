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
class DopplerProjectRoleNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("identifier")
    name: PropertyRef = PropertyRef("name")
    permissions: PropertyRef = PropertyRef("permissions")
    is_custom_role: PropertyRef = PropertyRef("is_custom_role")
    created_at: PropertyRef = PropertyRef("created_at")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DopplerProjectRoleToWorkplaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DopplerWorkplace)-[:RESOURCE]->(:DopplerProjectRole)
class DopplerProjectRoleToWorkplaceRel(CartographyRelSchema):
    target_node_label: str = "DopplerWorkplace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKPLACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DopplerProjectRoleToWorkplaceRelProperties = (
        DopplerProjectRoleToWorkplaceRelProperties()
    )


@dataclass(frozen=True)
class DopplerProjectRoleSchema(CartographyNodeSchema):
    label: str = "DopplerProjectRole"
    properties: DopplerProjectRoleNodeProperties = DopplerProjectRoleNodeProperties()
    sub_resource_relationship: DopplerProjectRoleToWorkplaceRel = (
        DopplerProjectRoleToWorkplaceRel()
    )
