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
class CircleCIContextNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="CircleCI context ID.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last update.",
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Context name."
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Context creation timestamp."
    )


@dataclass(frozen=True)
class CircleCIContextToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:CircleCIOrganization)-[:RESOURCE]->(:CircleCIContext)
class CircleCIContextToOrganizationRel(CartographyRelSchema):
    """The CircleCI organization contains the context."""

    target_node_label: str = "CircleCIOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: CircleCIContextToOrganizationRelProperties = (
        CircleCIContextToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class CircleCIContextToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:CircleCIContext)-[:RESTRICTED_TO]->(:CircleCIProject)
# One-to-many: a context's restrictions name the projects allowed to use it.
# The project ids come from /context/{id}/restrictions and are attached to the
# context row as `restricted_project_ids`. Best-effort: OPTIONAL MATCH, so only
# projects already ingested are linked.
class CircleCIContextToProjectRel(CartographyRelSchema):
    """The context is restricted to the allowed CircleCI projects."""

    target_node_label: str = "CircleCIProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("restricted_project_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RESTRICTED_TO"
    properties: CircleCIContextToProjectRelProperties = (
        CircleCIContextToProjectRelProperties()
    )


@dataclass(frozen=True)
class CircleCIContextSchema(CartographyNodeSchema):
    """A CircleCI context containing shared environment variables."""

    label: str = "CircleCIContext"
    properties: CircleCIContextNodeProperties = CircleCIContextNodeProperties()
    sub_resource_relationship: CircleCIContextToOrganizationRel = (
        CircleCIContextToOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [CircleCIContextToProjectRel()],
    )
