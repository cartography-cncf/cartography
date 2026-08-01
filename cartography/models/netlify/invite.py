from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_source_node_matcher
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import SourceNodeMatcher
from cartography.models.core.relationships import TargetNodeMatcher


# --- Node Definitions ---
@dataclass(frozen=True)
class NetlifyInviteNodeProperties(CartographyNodeProperties):
    # An invited address has no Netlify user yet, so the email is the only identity available.
    id: PropertyRef = PropertyRef("email", description="The invited email address.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    email: PropertyRef = PropertyRef(
        "email", extra_index=True, description="The invited email address."
    )


# --- Relationship Definitions ---
@dataclass(frozen=True)
class NetlifyInviteToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label",
        set_in_kwargs=True,
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)


@dataclass(frozen=True)
# (:NetlifyAccount)-[:RESOURCE]->(:NetlifyInvite)
class NetlifyInviteToAccountMatchLink(CartographyRelSchema):
    """The team that issued the invitation. The same address can be invited to several teams."""

    source_node_label: str = "NetlifyInvite"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("email")},
    )
    target_node_label: str = "NetlifyAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("account_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: NetlifyInviteToAccountRelProperties = (
        NetlifyInviteToAccountRelProperties()
    )


@dataclass(frozen=True)
class NetlifyInvitationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    # Per team: the same address can be invited to several teams with a different role in each.
    membership_id: PropertyRef = PropertyRef(
        "membership_id", description="Id of the membership row holding the invitation."
    )
    role: PropertyRef = PropertyRef(
        "role", description="Role the address is invited to hold in this team."
    )
    site_access: PropertyRef = PropertyRef(
        "site_access",
        description="Site access the invitation grants (`all`, `none`, ...).",
    )
    # Netlify's own statements about the invitation, kept so the state is queryable rather than
    # implied by the node type.
    pending: PropertyRef = PropertyRef(
        "pending",
        description="Whether Netlify still reports the invitation as pending.",
    )
    invite_id: PropertyRef = PropertyRef(
        "invite_id", description="Netlify's id for the invitation, when it reports one."
    )
    self_invite_state: PropertyRef = PropertyRef(
        "self_invite_state",
        description="State of a self-service join request, when the address asked to join.",
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="When the invitation was issued."
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="When the invitation was last modified."
    )
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label",
        set_in_kwargs=True,
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)


@dataclass(frozen=True)
# (:NetlifyInvite)-[:INVITED_TO]->(:NetlifyAccount)
# Not MEMBER_OF: the address is not a member of anything until it accepts.
class NetlifyInvitedToAccountMatchLink(CartographyRelSchema):
    """
    An outstanding invitation to a team. Deliberately not a membership edge: the address is not
    a member of anything until it accepts.
    """

    source_node_label: str = "NetlifyInvite"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("email")},
    )
    target_node_label: str = "NetlifyAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("account_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "INVITED_TO"
    properties: NetlifyInvitationRelProperties = NetlifyInvitationRelProperties()


# --- Main Schema ---
@dataclass(frozen=True)
class NetlifyInviteSchema(CartographyNodeSchema):
    """
    An email address invited to a Netlify team that has not accepted yet.

    A team member is invited by email address alone, so the membership exists before any Netlify
    user is attached to it. NetlifyUser is keyed on the user id, so those rows get their own node
    keyed on the email, the only identity they have. An existing user invited to a further team
    is a NetlifyUser with a pending membership instead, since the person already exists.

    It carries no ontology label on purpose: there is no account behind the address, so calling
    it a user account would put a non-existent identity into cross-provider identity queries.

    The node is deleted once no team holds the invitation any more, which is what happens when it
    is accepted or revoked. An address still invited elsewhere survives.
    """

    label: str = "NetlifyInvite"
    properties: NetlifyInviteNodeProperties = NetlifyInviteNodeProperties()
    # Shared across teams like NetlifyUser, so the team edges are MatchLinks; see user.py.
    sub_resource_relationship = None
