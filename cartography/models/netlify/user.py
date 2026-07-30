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
from cartography.models.ontology.labels import USER_ACCOUNT


# --- Node Definitions ---
@dataclass(frozen=True)
class NetlifyUserNodeProperties(CartographyNodeProperties):
    # Netlify returns two ids on a membership: `id` identifies the membership row and
    # `user_id` identifies the person. We key on `user_id` so one human is one node even when
    # they belong to several teams, and keep the membership id on the MEMBER_OF edge.
    id: PropertyRef = PropertyRef("user_id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    email: PropertyRef = PropertyRef("email", extra_index=True)
    full_name: PropertyRef = PropertyRef("full_name")
    avatar: PropertyRef = PropertyRef("avatar")
    mfa_enabled: PropertyRef = PropertyRef("mfa_enabled")
    # True while an invitation is outstanding, i.e. the account cannot sign in yet.
    pending: PropertyRef = PropertyRef("pending")
    # Netlify reports activity as a date string, not a timestamp.
    last_activity_date: PropertyRef = PropertyRef("last_activity_date")
    managed_by_directory_sync: PropertyRef = PropertyRef("managed_by_directory_sync")
    # Identity providers this account has linked (for example {"google": "user@example.com"}),
    # flattened by transform() to a sorted list of provider names.
    connected_account_providers: PropertyRef = PropertyRef(
        "connected_account_providers",
    )
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")


# --- Relationship Definitions ---
@dataclass(frozen=True)
class NetlifyUserToNetlifyAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:NetlifyAccount)-[:RESOURCE]->(:NetlifyUser)
class NetlifyUserToNetlifyAccountRel(CartographyRelSchema):
    target_node_label: str = "NetlifyAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("NETLIFY_ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: NetlifyUserToNetlifyAccountRelProperties = (
        NetlifyUserToNetlifyAccountRelProperties()
    )


@dataclass(frozen=True)
class NetlifyUserMemberOfAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    # Membership-scoped facts live on the edge, not the node: the same person can hold a
    # different role in every team they belong to.
    membership_id: PropertyRef = PropertyRef("id")
    role: PropertyRef = PropertyRef("role")
    site_access: PropertyRef = PropertyRef("site_access")
    pending: PropertyRef = PropertyRef("pending")


@dataclass(frozen=True)
# (:NetlifyUser)-[:MEMBER_OF]->(:NetlifyAccount)
class NetlifyUserMemberOfAccountRel(CartographyRelSchema):
    target_node_label: str = "NetlifyAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("NETLIFY_ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF"
    properties: NetlifyUserMemberOfAccountRelProperties = (
        NetlifyUserMemberOfAccountRelProperties()
    )


# --- Main Schema ---
@dataclass(frozen=True)
class NetlifyUserSchema(CartographyNodeSchema):
    """
    A member of a Netlify team.
    """

    label: str = "NetlifyUser"
    properties: NetlifyUserNodeProperties = NetlifyUserNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([USER_ACCOUNT])
    sub_resource_relationship: NetlifyUserToNetlifyAccountRel = (
        NetlifyUserToNetlifyAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [NetlifyUserMemberOfAccountRel()],
    )
