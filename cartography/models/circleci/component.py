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
    id: PropertyRef = PropertyRef("id", description="CircleCI component ID.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last update.",
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Component name."
    )
    project_id: PropertyRef = PropertyRef(
        "project_id", description="ID of the associated CircleCI project."
    )
    labels: PropertyRef = PropertyRef(
        "labels", description="Labels assigned to the component."
    )
    release_count: PropertyRef = PropertyRef(
        "release_count", description="Number of component releases."
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Component creation timestamp."
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="Component update timestamp."
    )


@dataclass(frozen=True)
class CircleCIComponentToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:CircleCIOrganization)-[:RESOURCE]->(:CircleCIComponent)
class CircleCIComponentToOrganizationRel(CartographyRelSchema):
    """The CircleCI organization contains the deploy component."""

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
    """The CircleCI project has the deploy component."""

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
    """A deploy component in a CircleCI organization."""

    label: str = "CircleCIComponent"
    properties: CircleCIComponentNodeProperties = CircleCIComponentNodeProperties()
    sub_resource_relationship: CircleCIComponentToOrganizationRel = (
        CircleCIComponentToOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [CircleCIComponentToProjectRel()],
    )
