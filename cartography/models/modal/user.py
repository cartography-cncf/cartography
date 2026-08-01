"""Modal user accounts and their workspace memberships.

RE: why ModalUser carries no relationships on its node schema

A Modal user is a shared identity: the same person keeps the same ``us-...`` id across every
workspace they belong to, and Modal returns that id in each workspace's membership listing.

Two things follow, both about not letting one workspace's cleanup damage another's data:

* No ``sub_resource_relationship``. That would mark the user as owned by the workspace being
  synced, and the generated cleanup DETACH DELETEs any stale node hanging off it. A person who
  leaves workspace A but stays in workspace B would be deleted by A's sync, taking B's
  membership and any edge another module added to that identity with them. RailwayUser and
  GitHubUser have the same property and are modelled the same way.

* No ``other_relationships`` either. Relationship cleanup for a schema without a sub-resource
  is generated without an id filter, so syncing one workspace would delete every *other*
  workspace's stale edges before those workspaces had a chance to refresh them. The workspace
  edges are therefore MatchLinks, whose cleanup is scoped by ``_sub_resource_id`` to the
  workspace actually being synced.

The cost of this, accepted deliberately: a ModalUser node is never deleted, so a person who
leaves every workspace lingers as a node with no MEMBER_OF edge. An orphan node is a far
smaller problem than destroying a live workspace's membership data.

The split between person-level and membership-level data follows from the same reasoning.
Modal returns both in one record, but only the person-level fields belong on the node; the
membership-level ones (role, join date, removal date) are per-workspace and ride on the
MEMBER_OF relationship.
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
class ModalUserNodeProperties(CartographyNodeProperties):
    # The global Modal user id. Stable for one person across every workspace.
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    email: PropertyRef = PropertyRef("email", extra_index=True)
    # Modal's display name doubles as the workspace username: it is the value the API uses to
    # attribute object creation.
    display_name: PropertyRef = PropertyRef("display_name", extra_index=True)
    # GITHUB, OKTA or GOOGLE_OAUTH. A non-SSO provider in an SSO-managed workspace is a
    # finding, so this is indexed.
    identity_provider_type: PropertyRef = PropertyRef(
        "identity_provider_type", extra_index=True
    )
    idp_external_id: PropertyRef = PropertyRef("idp_external_id")
    avatar_url: PropertyRef = PropertyRef("avatar_url")
    # NOTE: member_id, member_role, joined_at, last_active_at and deleted_at are deliberately
    # absent. They describe one *membership*, not the person, so they live on the MEMBER_OF
    # relationship below. Putting deleted_at here would be actively wrong: a person removed
    # from one workspace but active in another would read as globally inactive.


@dataclass(frozen=True)
# A shared identity, so no sub-resource and no node relationships. See the module docstring.
class ModalUserSchema(CartographyNodeSchema):
    label: str = "ModalUser"
    properties: ModalUserNodeProperties = ModalUserNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([USER_ACCOUNT])


@dataclass(frozen=True)
class ModalUserMemberOfWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    # The membership's own id (`me-...`), which is per-workspace unlike the user id.
    member_id: PropertyRef = PropertyRef("member_id")
    # Raw MEMBER_ROLE_* value. Also expressed as a HAS_ROLE edge to a ModalWorkspaceRole node,
    # which is what the cross-provider UserAccount -> PermissionRole rules consume; kept here
    # too so the role is readable straight off the membership.
    member_role: PropertyRef = PropertyRef("member_role")
    joined_at: PropertyRef = PropertyRef("joined_at")
    last_active_at: PropertyRef = PropertyRef("last_active_at")
    # Set when the membership was removed from this workspace specifically.
    deleted_at: PropertyRef = PropertyRef("deleted_at")
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ModalUser)-[:MEMBER_OF]->(:ModalWorkspace)
class ModalUserMemberOfWorkspaceMatchLink(CartographyRelSchema):
    source_node_label: str = "ModalUser"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("user_id")},
    )
    target_node_label: str = "ModalWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("workspace_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF"
    properties: ModalUserMemberOfWorkspaceRelProperties = (
        ModalUserMemberOfWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class ModalUserToWorkspaceRoleRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ModalUser)-[:HAS_ROLE]->(:ModalWorkspaceRole)
# HAS_ROLE is the canonical UserAccount -> PermissionRole label in ONTOLOGY_REL_CONSTRAINTS, so
# the workspace role is expressed as an edge to a role node and not only as a property. A
# MatchLink rather than a node relationship, because ModalUser must stay free of both a
# sub-resource and node relationships (see the module docstring).
class ModalUserToWorkspaceRoleMatchLink(CartographyRelSchema):
    source_node_label: str = "ModalUser"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("user_id")},
    )
    target_node_label: str = "ModalWorkspaceRole"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("workspace_role_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_ROLE"
    properties: ModalUserToWorkspaceRoleRelProperties = (
        ModalUserToWorkspaceRoleRelProperties()
    )
