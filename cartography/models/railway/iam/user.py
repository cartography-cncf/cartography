"""
RE: why RailwayUser carries no relationships on its node schema

A Railway user is a shared identity. The same person can belong to several workspaces, and a
project member need not be a member of the containing workspace at all.

Two things follow, and both are about not letting one workspace's cleanup damage another's
data:

* No ``sub_resource_relationship``. That would mark the user as owned by the workspace being
  synced, and the generated cleanup DETACH DELETEs any stale node hanging off it - taking
  the other workspaces' relationships, and any edge another module added to that identity,
  with it. GitHubUser has the same property and is modelled the same way.

* No ``other_relationships`` either. Relationship cleanup for a schema without a sub
  resource is generated as ``MATCH (n:RailwayUser)<-[r:RESOURCE]-(:RailwayWorkspace)`` with
  no id filter, so syncing one workspace would delete every *other* workspace's stale edges
  before those workspaces had a chance to refresh them. A workspace whose sync then failed
  would silently lose its memberships. The workspace edges are therefore MatchLinks, whose
  cleanup is scoped by ``_sub_resource_id`` to the workspace actually being synced.

RE: two schemas on the same label

Railway reports members in two places. ``workspace.members`` carries a workspace role and a
2FA flag; ``project.members`` carries neither. Loading a project-only member through the
workspace schema would blank ``two_factor_auth_enabled`` for someone who is a full member of
another workspace, so each source gets a schema, as GitHub does for affiliated and
unaffiliated users.
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
from cartography.models.railway.extra_labels import RAILWAY_PRINCIPAL

# RailwayPrincipal: cross-provider IAM principal umbrella, mirroring AWSPrincipal /
# ScalewayPrincipal. UserAccount drives the ontology mapping.
_USER_LABELS = ExtraNodeLabels([USER_ACCOUNT, RAILWAY_PRINCIPAL])


@dataclass(frozen=True)
class RailwayUserNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="ID of the Railway user.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    email: PropertyRef = PropertyRef(
        "email", extra_index=True, description="Email address of the user."
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Display name of the user."
    )
    two_factor_auth_enabled: PropertyRef = PropertyRef(
        "twoFactorAuthEnabled",
        description="Whether the user has two-factor authentication enabled.",
    )


@dataclass(frozen=True)
class RailwayProjectMemberUserNodeProperties(CartographyNodeProperties):
    """
    Project members, without two_factor_auth_enabled: Railway does not report it on the
    project membership payload, and writing it would blank a value another workspace's sync
    established for the same person.
    """

    id: PropertyRef = PropertyRef("id", description="ID of the Railway user.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    email: PropertyRef = PropertyRef(
        "email", extra_index=True, description="Email address of the user."
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Display name of the user."
    )


@dataclass(frozen=True)
class RailwayUserSchema(CartographyNodeSchema):
    """A Railway user who is a member of a workspace."""

    label: str = "RailwayUser"
    extra_node_labels: ExtraNodeLabels = _USER_LABELS
    properties: RailwayUserNodeProperties = RailwayUserNodeProperties()
    sub_resource_relationship = None


@dataclass(frozen=True)
class RailwayProjectMemberUserSchema(CartographyNodeSchema):
    """A Railway user discovered through project membership."""

    label: str = "RailwayUser"
    extra_node_labels: ExtraNodeLabels = _USER_LABELS
    properties: RailwayProjectMemberUserNodeProperties = (
        RailwayProjectMemberUserNodeProperties()
    )
    sub_resource_relationship = None


@dataclass(frozen=True)
class RailwayUserToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label",
        set_in_kwargs=True,
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)


@dataclass(frozen=True)
# (:RailwayWorkspace)-[:RESOURCE]->(:RailwayUser)
# Every user the workspace's sync saw, whether a workspace member or only a project member.
class RailwayUserToWorkspaceMatchLink(CartographyRelSchema):
    """Connects a Railway workspace to a user discovered within its scope."""

    source_node_label: str = "RailwayUser"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("user_id")},
    )
    target_node_label: str = "RailwayWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("workspace_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: RailwayUserToWorkspaceRelProperties = (
        RailwayUserToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class RailwayWorkspaceMembershipRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    role: PropertyRef = PropertyRef(
        "role",
        description="Role granted to the user in the workspace.",
    )
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label",
        set_in_kwargs=True,
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)


@dataclass(frozen=True)
# (:RailwayUser)-[:MEMBER_OF]->(:RailwayWorkspace)
# Only for actual workspace members. A project-only member gets the RESOURCE edge above but
# not this one, and their project role rides on the project membership MatchLink instead.
class RailwayUserMemberOfWorkspaceMatchLink(CartographyRelSchema):
    """Represents a Railway user's membership and role in a workspace."""

    source_node_label: str = "RailwayUser"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("user_id")},
    )
    target_node_label: str = "RailwayWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("workspace_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF"
    properties: RailwayWorkspaceMembershipRelProperties = (
        RailwayWorkspaceMembershipRelProperties()
    )
