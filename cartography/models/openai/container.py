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


@dataclass(frozen=True)
class OpenAIContainerNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    object: PropertyRef = PropertyRef("object")
    name: PropertyRef = PropertyRef("name")
    status: PropertyRef = PropertyRef("status")
    created_at: PropertyRef = PropertyRef("created_at")
    last_active_at: PropertyRef = PropertyRef("last_active_at")
    memory_limit: PropertyRef = PropertyRef("memory_limit")


@dataclass(frozen=True)
class OpenAIContainerToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:OpenAIContainer)<-[:RESOURCE]-(:OpenAIProject)
class OpenAIContainerToProjectRel(CartographyRelSchema):
    target_node_label: str = "OpenAIProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("project_id", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: OpenAIContainerToProjectRelProperties = (
        OpenAIContainerToProjectRelProperties()
    )


@dataclass(frozen=True)
class OpenAIContainerSchema(CartographyNodeSchema):
    label: str = "OpenAIContainer"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["ComputeInstance"])
    properties: OpenAIContainerNodeProperties = OpenAIContainerNodeProperties()
    sub_resource_relationship: OpenAIContainerToProjectRel = (
        OpenAIContainerToProjectRel()
    )
