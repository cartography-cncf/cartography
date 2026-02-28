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
class OpenAISkillNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    object: PropertyRef = PropertyRef("object")
    name: PropertyRef = PropertyRef("name")
    description: PropertyRef = PropertyRef("description")
    created_at: PropertyRef = PropertyRef("created_at")
    default_version: PropertyRef = PropertyRef("default_version")
    latest_version: PropertyRef = PropertyRef("latest_version")


@dataclass(frozen=True)
class OpenAISkillToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:OpenAISkill)<-[:RESOURCE]-(:OpenAIProject)
class OpenAISkillToProjectRel(CartographyRelSchema):
    target_node_label: str = "OpenAIProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("project_id", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: OpenAISkillToProjectRelProperties = OpenAISkillToProjectRelProperties()


@dataclass(frozen=True)
class OpenAISkillSchema(CartographyNodeSchema):
    label: str = "OpenAISkill"
    properties: OpenAISkillNodeProperties = OpenAISkillNodeProperties()
    sub_resource_relationship: OpenAISkillToProjectRel = OpenAISkillToProjectRel()
