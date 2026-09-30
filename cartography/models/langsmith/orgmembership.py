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
class LangSmithOrgMembershipNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Synthetic identifier of the form <organization_id>|<ls_user_id>.",
    )
    identity_id: PropertyRef = PropertyRef(
        "identity_id",
        description=(
            "UUID of the organization-scoped identity row backing this membership. This is "
            "a membership identifier, not a user identifier."
        ),
    )
    ls_user_id: PropertyRef = PropertyRef(
        "ls_user_id",
        extra_index=True,
        description="Stable LangSmith user ID of the member.",
    )
    email: PropertyRef = PropertyRef(
        "email",
        description="Email address of the member, denormalized for convenience.",
    )
    role_name: PropertyRef = PropertyRef(
        "role_name", description="Display name of the organization role held."
    )
    is_disabled: PropertyRef = PropertyRef(
        "is_disabled",
        description=(
            "True if this organization identity is deactivated. Deactivated identities "
            "cannot authenticate, and their personal access tokens are rejected. This is "
            "per-organization state, which is why it is not on the user node."
        ),
    )
    is_pending: PropertyRef = PropertyRef(
        "is_pending",
        description="True if this is an outstanding invitation rather than an accepted membership.",
    )
    login_methods: PropertyRef = PropertyRef(
        "login_methods",
        description="Auth providers linked to this identity, for example email, oidc or saml.",
    )
    provisioning_methods: PropertyRef = PropertyRef(
        "provisioning_methods",
        description="How the identity's login methods were provisioned, for example scim or saml:jit.",
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Timestamp when the user joined the organization."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class LangSmithOrgMembershipToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:LangSmithOrganization)-[:RESOURCE]->(:LangSmithOrgMembership)
class LangSmithOrgMembershipToOrganizationRel(CartographyRelSchema):
    """Links an organization to one of its memberships."""

    target_node_label: str = "LangSmithOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: LangSmithOrgMembershipToOrganizationRelProperties = (
        LangSmithOrgMembershipToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class LangSmithOrgMembershipToUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:LangSmithUser)-[:HAS_MEMBERSHIP]->(:LangSmithOrgMembership)
class LangSmithOrgMembershipToUserRel(CartographyRelSchema):
    """Links a user to their membership of one organization."""

    target_node_label: str = "LangSmithUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ls_user_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_MEMBERSHIP"
    properties: LangSmithOrgMembershipToUserRelProperties = (
        LangSmithOrgMembershipToUserRelProperties()
    )


@dataclass(frozen=True)
class LangSmithOrgMembershipToRoleRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:LangSmithOrgMembership)-[:HAS_ROLE]->(:LangSmithRole)
class LangSmithOrgMembershipToRoleRel(CartographyRelSchema):
    """Links a membership to the organization role it confers."""

    target_node_label: str = "LangSmithRole"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("role_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_ROLE"
    properties: LangSmithOrgMembershipToRoleRelProperties = (
        LangSmithOrgMembershipToRoleRelProperties()
    )


@dataclass(frozen=True)
class LangSmithOrgMembershipSchema(CartographyNodeSchema):
    """
    A user's membership of a single organization, together with the role they hold there.

    Modelled as a node so that organization-specific state stays organization-specific: a
    user can belong to several organizations, and each has its own view of whether that
    identity is disabled, what role it holds and how it was provisioned.
    """

    label: str = "LangSmithOrgMembership"
    properties: LangSmithOrgMembershipNodeProperties = (
        LangSmithOrgMembershipNodeProperties()
    )
    sub_resource_relationship: LangSmithOrgMembershipToOrganizationRel = (
        LangSmithOrgMembershipToOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            LangSmithOrgMembershipToUserRel(),
            LangSmithOrgMembershipToRoleRel(),
        ],
    )
