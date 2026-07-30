from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.ontology.labels import API_KEY


@dataclass(frozen=True)
class RailwayProjectTokenNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")
    # Railway's own redacted prefix, not the secret itself.
    display_token: PropertyRef = PropertyRef("displayToken")
    project_id: PropertyRef = PropertyRef("projectId")
    # A project token is scoped to exactly one environment of the project.
    environment_id: PropertyRef = PropertyRef("environmentId", extra_index=True)
    created_at: PropertyRef = PropertyRef("createdAt")


@dataclass(frozen=True)
class RailwayProjectTokenToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:RailwayProject)-[:RESOURCE]->(:RailwayProjectToken)
class RailwayProjectTokenToProjectRel(CartographyRelSchema):
    target_node_label: str = "RailwayProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: RailwayProjectTokenToProjectRelProperties = (
        RailwayProjectTokenToProjectRelProperties()
    )


@dataclass(frozen=True)
class RailwayProjectTokenSchema(CartographyNodeSchema):
    label: str = "RailwayProjectToken"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([API_KEY])
    properties: RailwayProjectTokenNodeProperties = RailwayProjectTokenNodeProperties()
    sub_resource_relationship: RailwayProjectTokenToProjectRel = (
        RailwayProjectTokenToProjectRel()
    )
