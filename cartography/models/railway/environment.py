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
class RailwayEnvironmentNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="ID of the Railway environment.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Name of the environment."
    )
    project_id: PropertyRef = PropertyRef(
        "projectId", extra_index=True, description="ID of the owning project."
    )
    created_at: PropertyRef = PropertyRef(
        "createdAt", description="Time when the environment was created."
    )
    # Ephemeral environments are spun up per pull request and torn down on merge.
    is_ephemeral: PropertyRef = PropertyRef(
        "isEphemeral",
        description="Whether this is a short-lived pull-request environment.",
    )


@dataclass(frozen=True)
class RailwayEnvironmentToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:RailwayProject)-[:RESOURCE]->(:RailwayEnvironment)
class RailwayEnvironmentToProjectRel(CartographyRelSchema):
    """Connects a Railway project to an environment that it contains."""

    target_node_label: str = "RailwayProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: RailwayEnvironmentToProjectRelProperties = (
        RailwayEnvironmentToProjectRelProperties()
    )


@dataclass(frozen=True)
class RailwayEnvironmentSchema(CartographyNodeSchema):
    """A Railway deployment environment, such as production or staging."""

    label: str = "RailwayEnvironment"
    properties: RailwayEnvironmentNodeProperties = RailwayEnvironmentNodeProperties()
    sub_resource_relationship: RailwayEnvironmentToProjectRel = (
        RailwayEnvironmentToProjectRel()
    )
