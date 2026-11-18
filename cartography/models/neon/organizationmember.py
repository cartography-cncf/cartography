from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.ontology.labels import USER_ACCOUNT


@dataclass(frozen=True)
class NeonOrganizationMemberNodeProperties(CartographyNodeProperties):
    # The API returns a membership id distinct from the user id. A user in two
    # organizations has two memberships, each with its own role, so the
    # membership id is the right node key; the canonical `User` ontology node
    # unifies them back into one person by email.
    id: PropertyRef = PropertyRef(
        "id",
        description="The membership id. A user in several organizations has one membership, and so one node, per organization",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    user_id: PropertyRef = PropertyRef(
        "user_id",
        extra_index=True,
        description="The member's Neon user id, shared across their memberships",
    )
    org_id: PropertyRef = PropertyRef(
        "org_id",
        extra_index=True,
        description="Id of the organization this membership belongs to",
    )
    email: PropertyRef = PropertyRef(
        "email", extra_index=True, description="The member's email address"
    )
    role: PropertyRef = PropertyRef(
        "role",
        description="The member's role in the organization (`admin`, `member`, `editor`, `viewer`, `collaborator`)",
    )
    has_mfa: PropertyRef = PropertyRef(
        "has_mfa",
        description="Whether the member has multi-factor authentication enabled",
    )
    deactivated_at: PropertyRef = PropertyRef(
        "deactivated_at",
        description="When the member's user account was deactivated, if it was",
    )
    joined_at: PropertyRef = PropertyRef(
        "joined_at", description="When the member joined the organization"
    )


@dataclass(frozen=True)
class NeonOrganizationMemberToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:NeonOrganization)-[:RESOURCE]->(:NeonOrganizationMember)
class NeonOrganizationMemberToOrganizationRel(CartographyRelSchema):
    target_node_label: str = "NeonOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: NeonOrganizationMemberToOrganizationRelProperties = (
        NeonOrganizationMemberToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class NeonOrganizationMemberSchema(CartographyNodeSchema):
    """Represents a user's membership in a Neon organization, with the role it grants."""

    label: str = "NeonOrganizationMember"
    properties: NeonOrganizationMemberNodeProperties = (
        NeonOrganizationMemberNodeProperties()
    )
    sub_resource_relationship: NeonOrganizationMemberToOrganizationRel = (
        NeonOrganizationMemberToOrganizationRel()
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([USER_ACCOUNT])
