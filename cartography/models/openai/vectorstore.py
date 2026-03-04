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
class OpenAIVectorStoreNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    object: PropertyRef = PropertyRef("object")
    name: PropertyRef = PropertyRef("name")
    status: PropertyRef = PropertyRef("status")
    created_at: PropertyRef = PropertyRef("created_at")
    last_active_at: PropertyRef = PropertyRef("last_active_at")
    usage_bytes: PropertyRef = PropertyRef("usage_bytes")
    expires_at: PropertyRef = PropertyRef("expires_at")


@dataclass(frozen=True)
class OpenAIVectorStoreToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:OpenAIVectorStore)<-[:RESOURCE]-(:OpenAIProject)
class OpenAIVectorStoreToProjectRel(CartographyRelSchema):
    target_node_label: str = "OpenAIProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("project_id", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: OpenAIVectorStoreToProjectRelProperties = (
        OpenAIVectorStoreToProjectRelProperties()
    )


@dataclass(frozen=True)
class OpenAIVectorStoreSchema(CartographyNodeSchema):
    label: str = "OpenAIVectorStore"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Database"])
    properties: OpenAIVectorStoreNodeProperties = OpenAIVectorStoreNodeProperties()
    sub_resource_relationship: OpenAIVectorStoreToProjectRel = (
        OpenAIVectorStoreToProjectRel()
    )
