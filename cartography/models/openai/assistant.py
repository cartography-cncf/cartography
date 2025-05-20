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
class OpenAIAssistantNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    object: PropertyRef = PropertyRef("object")
    created_at: PropertyRef = PropertyRef("created_at")
    name: PropertyRef = PropertyRef("name")
    description: PropertyRef = PropertyRef("description")
    model: PropertyRef = PropertyRef("model")
    instructions: PropertyRef = PropertyRef("instructions")
    temperature: PropertyRef = PropertyRef("temperature")
    top_p: PropertyRef = PropertyRef("top_p")
    metadata_id: PropertyRef = PropertyRef("metadata.id")
    response_format_id: PropertyRef = PropertyRef("response_format.id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class OpenAIAssistantToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:OpenAIOrganization)-[:RESOURCE]->(:OpenAIAssistant)
class OpenAIAssistantToOrganizationRel(CartographyRelSchema):
    target_node_label: str = "OpenAIOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: OpenAIAssistantToOrganizationRelProperties = (
        OpenAIAssistantToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class OpenAIAssistantSchema(CartographyNodeSchema):
    label: str = "OpenAIAssistant"
    properties: OpenAIAssistantNodeProperties = OpenAIAssistantNodeProperties()
    sub_resource_relationship: OpenAIAssistantToOrganizationRel = (
        OpenAIAssistantToOrganizationRel()
    )
