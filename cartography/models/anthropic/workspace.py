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
class AnthropicWorkspaceNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    created_at: PropertyRef = PropertyRef("created_at")
    archived_at: PropertyRef = PropertyRef("archived_at")
    display_color: PropertyRef = PropertyRef("display_color")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AnthropicWorkspaceToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AnthropicOrganization)-[:RESOURCE]->(:AnthropicWorkspace)
class AnthropicWorkspaceToOrganizationRel(CartographyRelSchema):
    target_node_label: str = "AnthropicOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AnthropicWorkspaceToOrganizationRelProperties = (
        AnthropicWorkspaceToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class AnthropicWorkspaceToUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AnthropicUser)-[:MEMBER_OF]->(:AnthropicWorkspace)
class AnthropicWorkspaceToUserRel(CartographyRelSchema):
    target_node_label: str = "AnthropicUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("users", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "MEMBER_OF"
    properties: AnthropicWorkspaceToUserRelProperties = (
        AnthropicWorkspaceToUserRelProperties()
    )


@dataclass(frozen=True)
class AnthropicWorkspaceToUserAdminRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AnthropicUser)-[:ADMIN_OF]->(:AnthropicWorkspace)
class AnthropicWorkspaceToUserAdminRel(CartographyRelSchema):
    target_node_label: str = "AnthropicUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("admins", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "ADMIN_OF"
    properties: AnthropicWorkspaceToUserAdminRelProperties = (
        AnthropicWorkspaceToUserAdminRelProperties()
    )


@dataclass(frozen=True)
class AnthropicWorkspaceSchema(CartographyNodeSchema):
    label: str = "AnthropicWorkspace"
    properties: AnthropicWorkspaceNodeProperties = AnthropicWorkspaceNodeProperties()
    sub_resource_relationship: AnthropicWorkspaceToOrganizationRel = (
        AnthropicWorkspaceToOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [AnthropicWorkspaceToUserRel(), AnthropicWorkspaceToUserAdminRel()],
    )
