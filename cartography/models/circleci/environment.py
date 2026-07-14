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
class CircleCIEnvironmentNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="CircleCI environment ID.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last update.",
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Environment name."
    )
    description: PropertyRef = PropertyRef(
        "description", description="Environment description."
    )
    labels: PropertyRef = PropertyRef(
        "labels", description="Labels assigned to the environment."
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Environment creation timestamp."
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="Environment update timestamp."
    )


@dataclass(frozen=True)
class CircleCIEnvironmentToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:CircleCIOrganization)-[:RESOURCE]->(:CircleCIEnvironment)
class CircleCIEnvironmentToOrganizationRel(CartographyRelSchema):
    """The CircleCI organization contains the deploy environment."""

    target_node_label: str = "CircleCIOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: CircleCIEnvironmentToOrganizationRelProperties = (
        CircleCIEnvironmentToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class CircleCIEnvironmentSchema(CartographyNodeSchema):
    """A deploy environment in a CircleCI organization."""

    label: str = "CircleCIEnvironment"
    properties: CircleCIEnvironmentNodeProperties = CircleCIEnvironmentNodeProperties()
    sub_resource_relationship: CircleCIEnvironmentToOrganizationRel = (
        CircleCIEnvironmentToOrganizationRel()
    )
