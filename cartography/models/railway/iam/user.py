"""
RE: why RailwayUser has no sub_resource_relationship

A sub_resource_relationship marks a node as owned by its tenant, and the generated cleanup
job DETACH DELETEs any stale node hanging off the tenant being synced. A Railway user is not
owned by one workspace: the same person can belong to several, and when several workspaces
are synced in one run the first workspace's cleanup would delete a user it no longer sees,
taking the other workspaces' relationships - and any edge another module added to that
identity - with it.

So, as with GitHubUser, the workspace relationship is modelled as an ordinary
other_relationship. Cleanup then removes only the stale workspace edges and leaves the
shared identity node in place.

RE: two schemas on the same label

Railway exposes members in two places. `workspace.members` are members of the workspace
itself and carry a workspace role and a 2FA flag. `project.members` may be people with
access to a single project without being workspace members at all, and that payload carries
neither field.

Loading both through one schema would assert MEMBER_OF from every project-only member to the
workspace, which is simply untrue, and would blank two_factor_auth_enabled for a user who is
a full member of another workspace. Hence a schema per source, as GitHub does for affiliated
and unaffiliated users.
"""

from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher

# RailwayPrincipal: cross-provider IAM principal umbrella, mirroring AWSPrincipal /
# ScalewayPrincipal. UserAccount drives the ontology mapping.
_USER_LABELS = ExtraNodeLabels(["UserAccount", "RailwayPrincipal"])


@dataclass(frozen=True)
class RailwayUserNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    email: PropertyRef = PropertyRef("email", extra_index=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    two_factor_auth_enabled: PropertyRef = PropertyRef("twoFactorAuthEnabled")


@dataclass(frozen=True)
class RailwayProjectMemberUserNodeProperties(CartographyNodeProperties):
    """
    Project members without two_factor_auth_enabled: Railway does not report it on the
    project membership payload, and setting it would blank a value another workspace's sync
    established for the same person.
    """

    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    email: PropertyRef = PropertyRef("email", extra_index=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)


@dataclass(frozen=True)
class RailwayUserToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:RailwayWorkspace)-[:RESOURCE]->(:RailwayUser)
class RailwayUserToWorkspaceRel(CartographyRelSchema):
    target_node_label: str = "RailwayWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKSPACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: RailwayUserToWorkspaceRelProperties = (
        RailwayUserToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class RailwayUserMemberOfWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    role: PropertyRef = PropertyRef("role")


@dataclass(frozen=True)
# (:RailwayUser)-[:MEMBER_OF]->(:RailwayWorkspace)
# Only emitted for workspace members. A user's project role is a different thing and rides on
# the project membership MatchLink instead.
class RailwayUserMemberOfWorkspaceRel(CartographyRelSchema):
    target_node_label: str = "RailwayWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKSPACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF"
    properties: RailwayUserMemberOfWorkspaceRelProperties = (
        RailwayUserMemberOfWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class RailwayUserSchema(CartographyNodeSchema):
    """Members of the workspace itself."""

    label: str = "RailwayUser"
    extra_node_labels: ExtraNodeLabels = _USER_LABELS
    properties: RailwayUserNodeProperties = RailwayUserNodeProperties()
    # See the module docstring: a shared identity must not be DETACH DELETEd by one
    # workspace's cleanup.
    sub_resource_relationship = None
    other_relationships: OtherRelationships = OtherRelationships(
        [
            RailwayUserToWorkspaceRel(),
            RailwayUserMemberOfWorkspaceRel(),
        ],
    )


@dataclass(frozen=True)
class RailwayProjectMemberUserSchema(CartographyNodeSchema):
    """
    People reachable only through a project's member list.

    They get the workspace RESOURCE edge, because that is how the sync discovered them, but
    no MEMBER_OF: they are not members of the workspace.
    """

    label: str = "RailwayUser"
    extra_node_labels: ExtraNodeLabels = _USER_LABELS
    properties: RailwayProjectMemberUserNodeProperties = (
        RailwayProjectMemberUserNodeProperties()
    )
    sub_resource_relationship = None
    other_relationships: OtherRelationships = OtherRelationships(
        [
            RailwayUserToWorkspaceRel(),
        ],
    )
