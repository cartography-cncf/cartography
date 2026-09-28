"""
An Airbyte user is a shared identity: the same person can belong to several
organizations, and one sync visits every organization the application can see.
The user node therefore has no relationships of its own. With a
``sub_resource_relationship`` and ``other_relationships``, the generated cleanup
for one organization would delete the stale edges that another organization
wrote for a shared user, and delete a shared user who left this organization.

The organization and access edges are MatchLinks instead, so each
organization's cleanup only removes the edges it wrote (``_sub_resource_id``).
The node is never deleted: someone removed from every organization keeps a bare
node with no edges, like NetlifyUser, RailwayUser and GitHubUser.
"""

from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_source_node_matcher
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import SourceNodeMatcher
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.ontology.labels import USER_ACCOUNT


@dataclass(frozen=True)
class AirbyteUserNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Airbyte user ID.")
    name: PropertyRef = PropertyRef("name", description="User name.")
    email: PropertyRef = PropertyRef(
        "email", extra_index=True, description="User email address."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AirbyteUserMatchLinkRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AirbyteOrganization)-[:RESOURCE]->(:AirbyteUser)
class AirbyteUserToOrganizationMatchLink(CartographyRelSchema):
    """Links an organization to one of its users."""

    source_node_label: str = "AirbyteUser"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("user_id")},
    )
    target_node_label: str = "AirbyteOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("organization_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AirbyteUserMatchLinkRelProperties = AirbyteUserMatchLinkRelProperties()


@dataclass(frozen=True)
# (:AirbyteUser)-[:ADMIN_OF]->(:AirbyteOrganization)
class AirbyteUserAdminOfOrganizationMatchLink(CartographyRelSchema):
    """Links a user to an organization they administer."""

    source_node_label: str = "AirbyteUser"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("user_id")},
    )
    target_node_label: str = "AirbyteOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("scope_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ADMIN_OF"
    properties: AirbyteUserMatchLinkRelProperties = AirbyteUserMatchLinkRelProperties()


@dataclass(frozen=True)
# (:AirbyteUser)-[:ADMIN_OF]->(:AirbyteWorkspace)
class AirbyteUserAdminOfWorkspaceMatchLink(CartographyRelSchema):
    """Links a user to a workspace they administer."""

    source_node_label: str = "AirbyteUser"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("user_id")},
    )
    target_node_label: str = "AirbyteWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("scope_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ADMIN_OF"
    properties: AirbyteUserMatchLinkRelProperties = AirbyteUserMatchLinkRelProperties()


@dataclass(frozen=True)
# (:AirbyteUser)-[:MEMBER_OF]->(:AirbyteWorkspace)
class AirbyteUserMemberOfWorkspaceMatchLink(CartographyRelSchema):
    """Links a user to a workspace where they are a member."""

    source_node_label: str = "AirbyteUser"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("user_id")},
    )
    target_node_label: str = "AirbyteWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("scope_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF"
    properties: AirbyteUserMatchLinkRelProperties = AirbyteUserMatchLinkRelProperties()


@dataclass(frozen=True)
class AirbyteUserSchema(CartographyNodeSchema):
    """An Airbyte user account with the UserAccount label.

    The node is shared across organizations and never cleaned up. Traverse the
    RESOURCE edge from an organization to find its current users.
    """

    label: str = "AirbyteUser"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [USER_ACCOUNT]
    )  # UserAccount label is used for ontology mapping
    properties: AirbyteUserNodeProperties = AirbyteUserNodeProperties()
    sub_resource_relationship = None
