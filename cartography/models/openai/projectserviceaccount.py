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
class OpenAIProjectServiceAccountNodeProperties(CartographyNodeProperties):
    object: PropertyRef = PropertyRef("object")
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    role: PropertyRef = PropertyRef("role")
    created_at: PropertyRef = PropertyRef("created_at")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class OpenAIProjectServiceAccountToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:OpenAIProjectServiceAccount)<-[:RESOURCE]-(:OpenAIProject)
class OpenAIProjectServiceAccountToProjectRel(CartographyRelSchema):
    target_node_label: str = "OpenAIProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("project_id", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: OpenAIProjectServiceAccountToProjectRelProperties = (
        OpenAIProjectServiceAccountToProjectRelProperties()
    )


@dataclass(frozen=True)
class OpenAIProjectServiceAccountSchema(CartographyNodeSchema):
    label: str = "OpenAIProjectServiceAccount"
    properties: OpenAIProjectServiceAccountNodeProperties = (
        OpenAIProjectServiceAccountNodeProperties()
    )
    sub_resource_relationship: OpenAIProjectServiceAccountToProjectRel = (
        OpenAIProjectServiceAccountToProjectRel()
    )
