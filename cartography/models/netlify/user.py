"""
RE: why NetlifyUser carries no relationships on its node schema

A Netlify user is a shared identity. The same person can belong to several teams, holding a
different role in each, and one cartography run syncs exactly one team, so a multi-team estate
means several runs each with its own update tag. Both of the generated cleanup statements a
node-schema relationship would produce are unsafe here, and each was reproduced against a real
Neo4j before this was rewritten:

* No ``sub_resource_relationship``. It marks the user as owned by the team being synced, and the
  node cleanup is ``MATCH (n:NetlifyUser)<-[:RESOURCE]-(:NetlifyAccount{id: $NETLIFY_ACCOUNT_ID})
  WHERE n.lastupdated <> $UPDATE_TAG ... DETACH DELETE n``. Someone removed from this team but
  still in another one fails that predicate, because the other team's sync stamped a different
  tag, so the whole node goes and takes every other team's edges with it.

* No ``other_relationships`` either. The MEMBER_OF cleanup is generated as
  ``MATCH (n:NetlifyUser)<-[s:RESOURCE]-(:NetlifyAccount{id: $NETLIFY_ACCOUNT_ID})
  MATCH (n)-[r:MEMBER_OF]->(:NetlifyAccount) WHERE r.lastupdated <> $UPDATE_TAG DELETE r``. The
  account on the second MATCH is unconstrained, so syncing one team deletes the person's
  membership of every *other* team, whose edges legitimately carry an older tag. This one bites
  immediately, without anybody being removed from anything.

Both edges are therefore MatchLinks, whose cleanup is scoped by ``_sub_resource_id`` to the team
actually being synced. The node itself is never cleaned up: it is a shared identity that other
teams, and other modules, may still reference. RailwayUser and GitHubUser are modelled the same
way for the same reason.
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


# --- Node Definitions ---
@dataclass(frozen=True)
class NetlifyUserNodeProperties(CartographyNodeProperties):
    """
    Only facts about the person, never about one of their memberships.

    Netlify reports everything on a per-team membership payload, so anything team-scoped that
    landed here would be overwritten by whichever team's sync ran last. `pending`,
    `managed_by_directory_sync`, `role`, `site_access` and the membership timestamps are therefore
    all on the MEMBER_OF edge instead.
    """

    # Netlify returns two ids on a membership: `id` identifies the membership row and `user_id`
    # identifies the person. We key on `user_id` so one human is one node across teams.
    id: PropertyRef = PropertyRef(
        "user_id", description="The Netlify user id of the person."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    email: PropertyRef = PropertyRef(
        "email", extra_index=True, description="Email address."
    )
    full_name: PropertyRef = PropertyRef(
        "full_name",
        description="Display name. Netlify never splits this into first and last name.",
    )
    avatar: PropertyRef = PropertyRef("avatar", description="Avatar image URL.")
    # MFA is enrolled on the Netlify account itself, not per team.
    mfa_enabled: PropertyRef = PropertyRef(
        "mfa_enabled", description="Whether the account has MFA enabled."
    )
    # Netlify reports activity as a date string, not a timestamp.
    last_activity_date: PropertyRef = PropertyRef(
        "last_activity_date", description="Date of last activity, as a date string."
    )
    # Identity providers this account has linked (for example {"google": "user@example.com"}),
    # flattened by transform() to a sorted list of provider names.
    connected_account_providers: PropertyRef = PropertyRef(
        "connected_account_providers",
        description='Identity providers linked to the account, e.g. `["google"]`.',
    )


# --- Relationship Definitions ---
@dataclass(frozen=True)
class NetlifyUserToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label",
        set_in_kwargs=True,
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)


@dataclass(frozen=True)
# (:NetlifyAccount)-[:RESOURCE]->(:NetlifyUser)
class NetlifyUserToAccountMatchLink(CartographyRelSchema):
    """The team this person is a member of. The identity itself is shared across teams."""

    source_node_label: str = "NetlifyUser"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("user_id")},
    )
    target_node_label: str = "NetlifyAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("account_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: NetlifyUserToAccountRelProperties = NetlifyUserToAccountRelProperties()


@dataclass(frozen=True)
class NetlifyUserMembershipRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    # Membership-scoped facts live on the edge, not the node: the same person holds a different
    # role, a different site access grant and a different invitation state in every team they
    # belong to, and the timestamps are the membership row's rather than the account's.
    membership_id: PropertyRef = PropertyRef(
        "membership_id", description="Id of the membership row in this team."
    )
    role: PropertyRef = PropertyRef(
        "role", description="Role held in this team, e.g. `Owner`, `Collaborator`."
    )
    site_access: PropertyRef = PropertyRef(
        "site_access",
        description="Which of the team's sites this member can reach (`all`, `none`, ...).",
    )
    # True while an invitation to this team is outstanding. An existing Netlify user invited to a
    # further team arrives here, not as a NetlifyInvite: the person already exists.
    pending: PropertyRef = PropertyRef(
        "pending",
        description="Whether an invitation to this team is still outstanding.",
    )
    invite_id: PropertyRef = PropertyRef(
        "invite_id", description="Id of the outstanding invitation, when there is one."
    )
    managed_by_directory_sync: PropertyRef = PropertyRef(
        "managed_by_directory_sync",
        description="Whether this membership is provisioned by directory sync.",
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="When the membership was created."
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="When the membership was last modified."
    )
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label",
        set_in_kwargs=True,
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)


@dataclass(frozen=True)
# (:NetlifyUser)-[:MEMBER_OF]->(:NetlifyAccount)
class NetlifyUserMemberOfAccountMatchLink(CartographyRelSchema):
    """
    Membership of a team. Everything that varies per team is carried here rather than on the
    person, because the same human holds a different role, site access grant and invitation
    state in every team they belong to. `pending` in particular is per team, so whether someone
    is active is a fact about the membership, not about the identity.
    """

    source_node_label: str = "NetlifyUser"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("user_id")},
    )
    target_node_label: str = "NetlifyAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("account_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF"
    properties: NetlifyUserMembershipRelProperties = (
        NetlifyUserMembershipRelProperties()
    )


# --- Main Schema ---
@dataclass(frozen=True)
class NetlifyUserSchema(CartographyNodeSchema):
    """
    A member of a Netlify team, keyed on the person rather than on the membership row, so one
    human is one node even when they belong to several teams.

    The node is never deleted by a team's cleanup: other teams and other modules may still
    reference the identity. Removing someone from a team drops that team's edges and leaves a
    bare node behind, so ask who is on a team by traversing the membership edge rather than by
    node existence.

    A membership Netlify has not linked a user to becomes a NetlifyInvite instead. The split is
    on whether a user exists, not on whether the membership is pending: someone who already has
    a Netlify account and is invited to a further team stays a NetlifyUser with a pending
    membership.
    """

    label: str = "NetlifyUser"
    properties: NetlifyUserNodeProperties = NetlifyUserNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([USER_ACCOUNT])
    sub_resource_relationship = None
