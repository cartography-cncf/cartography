from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_source_node_matcher
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import SourceNodeMatcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class KeycloakMatchLinkRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label",
        set_in_kwargs=True,
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)


@dataclass(frozen=True)
class KeycloakUserInheritedMemberOfGroupMatchLink(CartographyRelSchema):
    target_node_label: str = "KeycloakGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("group_id")},
    )
    source_node_label: str = "KeycloakUser"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("user_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "INHERITED_MEMBER_OF"
    properties: KeycloakMatchLinkRelProperties = KeycloakMatchLinkRelProperties()


@dataclass(frozen=True)
class KeycloakRoleIndirectGrantsScopeMatchLink(CartographyRelSchema):
    target_node_label: str = "KeycloakScope"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("scope_id")},
    )
    source_node_label: str = "KeycloakRole"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("role_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "INDIRECT_GRANTS"
    properties: KeycloakMatchLinkRelProperties = KeycloakMatchLinkRelProperties()


@dataclass(frozen=True)
class KeycloakUserAssumeScopeMatchLink(CartographyRelSchema):
    target_node_label: str = "KeycloakScope"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("scope_id")},
    )
    source_node_label: str = "KeycloakUser"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("user_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ASSUME_SCOPE"
    properties: KeycloakMatchLinkRelProperties = KeycloakMatchLinkRelProperties()
