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
class DopplerServiceAccountNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("slug")
    name: PropertyRef = PropertyRef("name")
    created_at: PropertyRef = PropertyRef("created_at")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DopplerServiceAccountToWorkplaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DopplerWorkplace)-[:RESOURCE]->(:DopplerServiceAccount)
class DopplerServiceAccountToWorkplaceRel(CartographyRelSchema):
    target_node_label: str = "DopplerWorkplace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKPLACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DopplerServiceAccountToWorkplaceRelProperties = (
        DopplerServiceAccountToWorkplaceRelProperties()
    )


@dataclass(frozen=True)
class DopplerServiceAccountToRoleRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DopplerServiceAccount)-[:HAS_ROLE]->(:DopplerWorkplaceRole)
class DopplerServiceAccountToRoleRel(CartographyRelSchema):
    target_node_label: str = "DopplerWorkplaceRole"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("workplace_role")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_ROLE"
    properties: DopplerServiceAccountToRoleRelProperties = (
        DopplerServiceAccountToRoleRelProperties()
    )


@dataclass(frozen=True)
class DopplerServiceAccountSchema(CartographyNodeSchema):
    label: str = "DopplerServiceAccount"
    properties: DopplerServiceAccountNodeProperties = (
        DopplerServiceAccountNodeProperties()
    )
    sub_resource_relationship: DopplerServiceAccountToWorkplaceRel = (
        DopplerServiceAccountToWorkplaceRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [DopplerServiceAccountToRoleRel()],
    )
