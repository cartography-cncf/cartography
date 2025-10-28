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
class OpenAIUserNodeProperties(CartographyNodeProperties):
    object: PropertyRef = PropertyRef("object")
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    email: PropertyRef = PropertyRef("email", extra_index=True)
    role: PropertyRef = PropertyRef("role")
    added_at: PropertyRef = PropertyRef("added_at")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class OpenAIUserToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:OpenAIOrganization)-[:RESOURCE]->(:OpenAIUser)
class OpenAIUserToOrganizationRel(CartographyRelSchema):
    target_node_label: str = "OpenAIOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: OpenAIUserToOrganizationRelProperties = (
        OpenAIUserToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class OpenAIUserSchema(CartographyNodeSchema):
    label: str = "OpenAIUser"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        ["UserAccount"]
    )  # UserAccount label is used for ontology mapping
    properties: OpenAIUserNodeProperties = OpenAIUserNodeProperties()
    sub_resource_relationship: OpenAIUserToOrganizationRel = (
        OpenAIUserToOrganizationRel()
    )
