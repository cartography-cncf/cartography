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
class CircleCIPipelineNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    number: PropertyRef = PropertyRef("number")
    state: PropertyRef = PropertyRef("state")
    project_slug: PropertyRef = PropertyRef("project_slug")
    trigger_type: PropertyRef = PropertyRef("trigger_type")
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")


@dataclass(frozen=True)
class CircleCIPipelineToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:CircleCIProject)-[:RESOURCE]->(:CircleCIPipeline)
class CircleCIPipelineToProjectRel(CartographyRelSchema):
    target_node_label: str = "CircleCIProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: CircleCIPipelineToProjectRelProperties = (
        CircleCIPipelineToProjectRelProperties()
    )


@dataclass(frozen=True)
class CircleCIPipelineSchema(CartographyNodeSchema):
    label: str = "CircleCIPipeline"
    properties: CircleCIPipelineNodeProperties = CircleCIPipelineNodeProperties()
    sub_resource_relationship: CircleCIPipelineToProjectRel = (
        CircleCIPipelineToProjectRel()
    )
