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
class OpenAIProjectApiKeyNodeProperties(CartographyNodeProperties):
    object: PropertyRef = PropertyRef("object")
    redacted_value: PropertyRef = PropertyRef("redacted_value")
    name: PropertyRef = PropertyRef("name")
    created_at: PropertyRef = PropertyRef("created_at")
    last_used_at: PropertyRef = PropertyRef("last_used_at")
    id: PropertyRef = PropertyRef("id")
    # WIP: Map to other nodes
    owner_type: PropertyRef = PropertyRef("owner.type")
    owner_user: PropertyRef = PropertyRef("owner.user")
    owner_service_account: PropertyRef = PropertyRef("owner.service_account")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class OpenAIProjectApiKeyToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:OpenAIProjectApiKey)<-[:RESOURCE]-(:OpenAIProject)
class OpenAIProjectApiKeyToProjectRel(CartographyRelSchema):
    target_node_label: str = "OpenAIProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("project_id", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: OpenAIProjectApiKeyToProjectRelProperties = (
        OpenAIProjectApiKeyToProjectRelProperties()
    )


@dataclass(frozen=True)
class OpenAIProjectApiKeySchema(CartographyNodeSchema):
    label: str = "OpenAIProjectApiKey"
    properties: OpenAIProjectApiKeyNodeProperties = OpenAIProjectApiKeyNodeProperties()
    sub_resource_relationship: OpenAIProjectApiKeyToProjectRel = (
        OpenAIProjectApiKeyToProjectRel()
    )
