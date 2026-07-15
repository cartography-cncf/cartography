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
class WorkOSInvitationNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="WorkOS invitation ID.")
    email: PropertyRef = PropertyRef(
        "email", extra_index=True, description="Email address of the invited user."
    )
    state: PropertyRef = PropertyRef("state", description="Invitation state.")
    organization_id: PropertyRef = PropertyRef(
        "organization_id",
        extra_index=True,
        description="ID of the organization receiving the invitee.",
    )
    inviter_user_id: PropertyRef = PropertyRef(
        "inviter_user_id", description="ID of the user who created the invitation."
    )
    expires_at: PropertyRef = PropertyRef(
        "expires_at", description="RFC 3339 timestamp when the invitation expires."
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="RFC 3339 timestamp when the invitation was created."
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="RFC 3339 timestamp when the invitation was updated."
    )
    accepted_at: PropertyRef = PropertyRef(
        "accepted_at",
        description="RFC 3339 timestamp when the invitation was accepted.",
    )
    revoked_at: PropertyRef = PropertyRef(
        "revoked_at", description="RFC 3339 timestamp when the invitation was revoked."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Timestamp of the last update."
    )


@dataclass(frozen=True)
class WorkOSInvitationToEnvironmentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:WorkOSEnvironment)-[:RESOURCE]->(:WorkOSInvitation)
class WorkOSInvitationToEnvironmentRel(CartographyRelSchema):
    """The WorkOS environment contains this invitation as a resource."""

    target_node_label: str = "WorkOSEnvironment"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKOS_CLIENT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: WorkOSInvitationToEnvironmentRelProperties = (
        WorkOSInvitationToEnvironmentRelProperties()
    )


@dataclass(frozen=True)
class WorkOSInvitationToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:WorkOSInvitation)-[:FOR_ORGANIZATION]->(:WorkOSOrganization)
class WorkOSInvitationToOrganizationRel(CartographyRelSchema):
    """The WorkOS invitation is for its organization."""

    target_node_label: str = "WorkOSOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("organization_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "FOR_ORGANIZATION"
    properties: WorkOSInvitationToOrganizationRelProperties = (
        WorkOSInvitationToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class WorkOSInvitationToInviteeRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:WorkOSInvitation)-[:INVITES]->(:WorkOSUser)
class WorkOSInvitationToInviteeRel(CartographyRelSchema):
    """The WorkOS invitation invites the user with the matching email address."""

    target_node_label: str = "WorkOSUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"email": PropertyRef("email")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "INVITES"
    properties: WorkOSInvitationToInviteeRelProperties = (
        WorkOSInvitationToInviteeRelProperties()
    )


@dataclass(frozen=True)
class WorkOSInvitationToInviterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:WorkOSInvitation)-[:INVITED_BY]->(:WorkOSUser)
class WorkOSInvitationToInviterRel(CartographyRelSchema):
    """The WorkOS invitation was created by its inviter user."""

    target_node_label: str = "WorkOSUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("inviter_user_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "INVITED_BY"
    properties: WorkOSInvitationToInviterRelProperties = (
        WorkOSInvitationToInviterRelProperties()
    )


@dataclass(frozen=True)
class WorkOSInvitationSchema(CartographyNodeSchema):
    """An invitation to join a WorkOS organization."""

    label: str = "WorkOSInvitation"
    properties: WorkOSInvitationNodeProperties = WorkOSInvitationNodeProperties()
    sub_resource_relationship: WorkOSInvitationToEnvironmentRel = (
        WorkOSInvitationToEnvironmentRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        rels=[
            WorkOSInvitationToOrganizationRel(),
            WorkOSInvitationToInviteeRel(),
            WorkOSInvitationToInviterRel(),
        ],
    )
