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
class CircleCIProjectEnvVarNodeProperties(CartographyNodeProperties):
    # Synthesized stable id: "{project_slug}:{name}" (API returns no id here).
    id: PropertyRef = PropertyRef(
        "id", description="Synthesized project environment variable ID."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last update.",
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Environment variable name."
    )
    project_slug: PropertyRef = PropertyRef(
        "project_slug", description="Slug of the owning CircleCI project."
    )
    # The API only ever returns a masked value ("xxxx" + last 4 chars); the real
    # secret is never exposed, so this is the most we can store.
    value: PropertyRef = PropertyRef(
        "value", description="Masked environment variable value."
    )


@dataclass(frozen=True)
class CircleCIProjectEnvVarToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:CircleCIProject)-[:RESOURCE]->(:CircleCIProjectEnvVar)
class CircleCIProjectEnvVarToProjectRel(CartographyRelSchema):
    """The CircleCI project contains the environment variable."""

    target_node_label: str = "CircleCIProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: CircleCIProjectEnvVarToProjectRelProperties = (
        CircleCIProjectEnvVarToProjectRelProperties()
    )


@dataclass(frozen=True)
class CircleCIProjectEnvVarSchema(CartographyNodeSchema):
    """A project-level CircleCI environment variable with a masked value."""

    label: str = "CircleCIProjectEnvVar"
    properties: CircleCIProjectEnvVarNodeProperties = (
        CircleCIProjectEnvVarNodeProperties()
    )
    sub_resource_relationship: CircleCIProjectEnvVarToProjectRel = (
        CircleCIProjectEnvVarToProjectRel()
    )
