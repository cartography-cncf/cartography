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
    id: PropertyRef = PropertyRef("email")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    email: PropertyRef = PropertyRef("email", extra_index=True)


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
    membership_id: PropertyRef = PropertyRef("membership_id")
    role: PropertyRef = PropertyRef("role")
    site_access: PropertyRef = PropertyRef("site_access")
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label",
        set_in_kwargs=True,
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)


@dataclass(frozen=True)
# (:NetlifyInvite)-[:INVITED_TO]->(:NetlifyAccount)
# Not MEMBER_OF: the address is not a member of anything until it accepts.
class NetlifyInvitedToAccountMatchLink(CartographyRelSchema):
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
    """An email address invited to a Netlify team that has not accepted yet."""

    label: str = "NetlifyInvite"
    properties: NetlifyInviteNodeProperties = NetlifyInviteNodeProperties()
    # Shared across teams like NetlifyUser, so the team edges are MatchLinks; see user.py.
    sub_resource_relationship = None
