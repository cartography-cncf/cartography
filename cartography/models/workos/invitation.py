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
    id: PropertyRef = PropertyRef("id")
    email: PropertyRef = PropertyRef("email", extra_index=True)
    state: PropertyRef = PropertyRef("state")
    organization_id: PropertyRef = PropertyRef("organization_id", extra_index=True)
    inviter_user_id: PropertyRef = PropertyRef("inviter_user_id")
    token: PropertyRef = PropertyRef("token")
    accept_invitation_url: PropertyRef = PropertyRef("accept_invitation_url")
    expires_at: PropertyRef = PropertyRef("expires_at")
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")
    accepted_at: PropertyRef = PropertyRef("accepted_at")
    revoked_at: PropertyRef = PropertyRef("revoked_at")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class WorkOSInvitationToEnvironmentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:WorkOSEnvironment)-[:RESOURCE]->(:WorkOSInvitation)
class WorkOSInvitationToEnvironmentRel(CartographyRelSchema):
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
