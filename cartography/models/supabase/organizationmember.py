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
class SupabaseOrganizationMemberNodeProperties(CartographyNodeProperties):
    # A membership, not a person: synthesised as "<org slug>/<user id>". `role_name`
    # is per-organization, so keying on user_id alone would make the last
    # organization synced overwrite the member's role in every other one. A user in
    # two organizations therefore gets one node per organization, the same way
    # AWSUser is scoped per account; the canonical `User` ontology node is what
    # unifies them back into a single person.
    id: PropertyRef = PropertyRef(
        "id",
        description="Synthesised as `<org slug>/<user id>`. This node is a membership, not a person: `role_name` is per-organization, so a user belonging to several organizations gets one node per organization, the same way `AWSUser` is scoped per account",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    user_id: PropertyRef = PropertyRef(
        "user_id",
        extra_index=True,
        description="The member's Supabase user id, shared across their memberships",
    )
    email: PropertyRef = PropertyRef(
        "email", extra_index=True, description="The member's email address"
    )
    user_name: PropertyRef = PropertyRef(
        "user_name", description="The member's username"
    )
    role_name: PropertyRef = PropertyRef(
        "role_name",
        description="The member's role in the organization (Owner, Administrator, Developer, ...)",
    )
    mfa_enabled: PropertyRef = PropertyRef(
        "mfa_enabled",
        description="Whether the member has multi-factor authentication enabled on their Supabase account",
    )


@dataclass(frozen=True)
class SupabaseOrganizationMemberToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SupabaseOrganization)-[:RESOURCE]->(:SupabaseOrganizationMember)
class SupabaseOrganizationMemberToOrganizationRel(CartographyRelSchema):
    target_node_label: str = "SupabaseOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_SLUG", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SupabaseOrganizationMemberToOrganizationRelProperties = (
        SupabaseOrganizationMemberToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class SupabaseOrganizationMemberSchema(CartographyNodeSchema):
    """Represents a user who is a member of a Supabase organization."""

    label: str = "SupabaseOrganizationMember"
    properties: SupabaseOrganizationMemberNodeProperties = (
        SupabaseOrganizationMemberNodeProperties()
    )
    sub_resource_relationship: SupabaseOrganizationMemberToOrganizationRel = (
        SupabaseOrganizationMemberToOrganizationRel()
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([USER_ACCOUNT])
