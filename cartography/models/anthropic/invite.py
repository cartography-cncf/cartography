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
class AnthropicInviteNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Anthropic invite ID.")
    email: PropertyRef = PropertyRef(
        "email",
        extra_index=True,
        description="Email address the invite was sent to.",
    )
    role: PropertyRef = PropertyRef(
        "role",
        description="Organization role the invitee will hold once they accept.",
    )
    status: PropertyRef = PropertyRef(
        "status",
        description="Invite status: pending, accepted, expired, or deleted.",
    )
    invited_at: PropertyRef = PropertyRef(
        "invited_at",
        description="RFC 3339 timestamp when the invite was sent.",
    )
    expires_at: PropertyRef = PropertyRef(
        "expires_at",
        description=(
            "RFC 3339 timestamp when the invite expires. Invites hard-expire after "
            "21 days and the window is not configurable."
        ),
    )
    accepted_at: PropertyRef = PropertyRef(
        "accepted_at",
        description=(
            "RFC 3339 timestamp when the invite was accepted. Empty while the invite "
            "is outstanding."
        ),
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AnthropicInviteToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AnthropicOrganization)-[:RESOURCE]->(:AnthropicInvite)
class AnthropicInviteToOrganizationRel(CartographyRelSchema):
    """The organization issued the invite."""

    target_node_label: str = "AnthropicOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AnthropicInviteToOrganizationRelProperties = (
        AnthropicInviteToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class AnthropicInviteToRbacGroupRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AnthropicInvite)-[:GRANTS_MEMBERSHIP_OF]->(:AnthropicRbacGroup)
class AnthropicInviteToRbacGroupRel(CartographyRelSchema):
    """The group the invitee joins on acceptance.

    Distinct from MEMBER_OF: nobody is in the group yet. This is a pending grant,
    and it only appears on Claude Enterprise organizations.
    """

    target_node_label: str = "AnthropicRbacGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("rbac_group_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "GRANTS_MEMBERSHIP_OF"
    properties: AnthropicInviteToRbacGroupRelProperties = (
        AnthropicInviteToRbacGroupRelProperties()
    )


@dataclass(frozen=True)
class AnthropicInviteSchema(CartographyNodeSchema):
    """A pending or historical invitation to join an Anthropic organization.

    An outstanding invite is an un-redeemed grant of the role it carries: whoever
    controls the invited mailbox can claim it.
    """

    label: str = "AnthropicInvite"
    properties: AnthropicInviteNodeProperties = AnthropicInviteNodeProperties()
    sub_resource_relationship: AnthropicInviteToOrganizationRel = (
        AnthropicInviteToOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AnthropicInviteToRbacGroupRel(),
        ],
    )
