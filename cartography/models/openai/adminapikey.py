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
class OpenAIAdminApiKeyNodeProperties(CartographyNodeProperties):
    object: PropertyRef = PropertyRef("object")
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    redacted_value: PropertyRef = PropertyRef("redacted_value")
    value: PropertyRef = PropertyRef("value")
    created_at: PropertyRef = PropertyRef("created_at")
    last_used_at: PropertyRef = PropertyRef("last_used_at")
    # WIP: Tranform and map to other nodes
    owner_type: PropertyRef = PropertyRef("owner.type")
    owner_object: PropertyRef = PropertyRef("owner.object")
    owner_id: PropertyRef = PropertyRef("owner.id")
    owner_name: PropertyRef = PropertyRef("owner.name")
    owner_created_at: PropertyRef = PropertyRef("owner.created_at")
    owner_role: PropertyRef = PropertyRef("owner.role")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class OpenAIAdminApiKeyToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:OpenAIOrganization)-[:RESOURCE]->(:OpenAIAdminApiKey)
class OpenAIAdminApiKeyToOrganizationRel(CartographyRelSchema):
    target_node_label: str = "OpenAIOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: OpenAIAdminApiKeyToOrganizationRelProperties = (
        OpenAIAdminApiKeyToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class OpenAIAdminApiKeySchema(CartographyNodeSchema):
    label: str = "OpenAIAdminApiKey"
    properties: OpenAIAdminApiKeyNodeProperties = OpenAIAdminApiKeyNodeProperties()
    sub_resource_relationship: OpenAIAdminApiKeyToOrganizationRel = (
        OpenAIAdminApiKeyToOrganizationRel()
    )
