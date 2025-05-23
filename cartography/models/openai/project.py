from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
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
class OpenAIProjectToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:OpenAIOrganization)-[:RESOURCE]->(:OpenAIProject)
class OpenAIProjectToOrganizationRel(CartographyRelSchema):
    target_node_label: str = "OpenAIOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: OpenAIProjectToOrganizationRelProperties = (
        OpenAIProjectToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class OpenAIProjectToUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:OpenAIUser)-[:MEMBER_OF]->(:OpenAIProject)
class OpenAIProjectToUserRel(CartographyRelSchema):
    target_node_label: str = "OpenAIUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("users", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "MEMBER_OF"
    properties: OpenAIProjectToUserRelProperties = OpenAIProjectToUserRelProperties()


@dataclass(frozen=True)
class OpenAIProjectToUserAdminRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:OpenAIUser)-[:ADMIN_OF]->(:OpenAIProject)
class OpenAIProjectToUserAdminRel(CartographyRelSchema):
    target_node_label: str = "OpenAIUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("admins", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "ADMIN_OF"
    properties: OpenAIProjectToUserAdminRelProperties = (
        OpenAIProjectToUserAdminRelProperties()
    )


@dataclass(frozen=True)
class OpenAIProjectSchema(CartographyNodeSchema):
    label: str = "OpenAIProject"
    properties: OpenAIProjectNodeProperties = OpenAIProjectNodeProperties()
    sub_resource_relationship: OpenAIProjectToOrganizationRel = (
        OpenAIProjectToOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [OpenAIProjectToUserRel(), OpenAIProjectToUserAdminRel()],
    )
