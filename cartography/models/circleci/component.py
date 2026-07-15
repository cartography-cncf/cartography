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
class CircleCIComponentNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    project_id: PropertyRef = PropertyRef("project_id")
    labels: PropertyRef = PropertyRef("labels")
    release_count: PropertyRef = PropertyRef("release_count")
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")


@dataclass(frozen=True)
class CircleCIComponentToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:CircleCIOrganization)-[:RESOURCE]->(:CircleCIComponent)
class CircleCIComponentToOrganizationRel(CartographyRelSchema):
    target_node_label: str = "CircleCIOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: CircleCIComponentToOrganizationRelProperties = (
        CircleCIComponentToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class CircleCIComponentToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:CircleCIProject)-[:HAS_COMPONENT]->(:CircleCIComponent)
class CircleCIComponentToProjectRel(CartographyRelSchema):
    target_node_label: str = "CircleCIProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("project_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_COMPONENT"
    properties: CircleCIComponentToProjectRelProperties = (
        CircleCIComponentToProjectRelProperties()
    )


@dataclass(frozen=True)
class CircleCIComponentSchema(CartographyNodeSchema):
    label: str = "CircleCIComponent"
    properties: CircleCIComponentNodeProperties = CircleCIComponentNodeProperties()
    sub_resource_relationship: CircleCIComponentToOrganizationRel = (
        CircleCIComponentToOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [CircleCIComponentToProjectRel()],
    )
