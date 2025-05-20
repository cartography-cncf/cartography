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
class OpenAIProjectNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    object: PropertyRef = PropertyRef("object")
    name: PropertyRef = PropertyRef("name")
    created_at: PropertyRef = PropertyRef("created_at")
    archived_at: PropertyRef = PropertyRef("archived_at")
    status: PropertyRef = PropertyRef("status")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class OpenAIProjectToOrganizationUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:OpenAIOrganization)-[:RESOURCE]->(:OpenAIProject)
class OpenAIProjectToOrganizationUserRel(CartographyRelSchema):
    target_node_label: str = "OpenAIOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RESOURCE"
    properties: OpenAIProjectToOrganizationUserRelProperties = (
        OpenAIProjectToOrganizationUserRelProperties()
    )


@dataclass(frozen=True)
class OpenAIProjectSchema(CartographyNodeSchema):
    label: str = "OpenAIProject"
    properties: OpenAIProjectNodeProperties = OpenAIProjectNodeProperties()
    sub_resource_relationship: OpenAIProjectToOrganizationUserRel = (
        OpenAIProjectToOrganizationUserRel()
    )
