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


@dataclass(frozen=True)
class LangSmithUserNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "ls_user_id",
        description=(
            "Stable LangSmith user ID. Used instead of the user_id field, which mirrors the "
            "first linked auth provider subject and is not stable across login methods."
        ),
    )
    ls_user_id: PropertyRef = PropertyRef(
        "ls_user_id", description="Stable LangSmith user ID."
    )
    email: PropertyRef = PropertyRef(
        "email", extra_index=True, description="User email address."
    )
    name: PropertyRef = PropertyRef("full_name", description="User full name.")
    display_name: PropertyRef = PropertyRef(
        "display_name", description="User display name."
    )
    avatar_url: PropertyRef = PropertyRef(
        "avatar_url", description="URL of the user's avatar image."
    )
    is_disabled: PropertyRef = PropertyRef(
        "is_disabled",
        description=(
            "True if the identity is deactivated. Deactivated identities cannot authenticate, "
            "and their personal access tokens are rejected."
        ),
    )
    is_pending: PropertyRef = PropertyRef(
        "is_pending",
        description="True if this is an outstanding invitation rather than an accepted membership.",
    )
    login_methods: PropertyRef = PropertyRef(
        "login_methods",
        description=(
            "Auth providers linked to this user, for example email, oidc or saml."
        ),
    )
    provisioning_methods: PropertyRef = PropertyRef(
        "provisioning_methods",
        description="How the user's login methods were provisioned, for example scim or saml:jit.",
    )
    org_identity_id: PropertyRef = PropertyRef(
        "org_identity_id",
        description=(
            "UUID of the organization-scoped identity row for this user. This is a membership "
            "identifier, not a user identifier."
        ),
    )
    org_role_name: PropertyRef = PropertyRef(
        "org_role_name", description="Display name of the user's organization role."
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Timestamp when the user joined the organization."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class LangSmithUserToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:LangSmithOrganization)-[:RESOURCE]->(:LangSmithUser)
class LangSmithUserToOrganizationRel(CartographyRelSchema):
    """Links an organization to one of its users."""

    target_node_label: str = "LangSmithOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: LangSmithUserToOrganizationRelProperties = (
        LangSmithUserToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class LangSmithUserToOrgRoleRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# Canonical ontology edge: (:UserAccount)-[:HAS_ROLE]->(:PermissionRole)
# (:LangSmithUser)-[:HAS_ROLE]->(:LangSmithRole)
class LangSmithUserToOrgRoleRel(CartographyRelSchema):
    """
    A user holds an organization-scoped role.

    Workspace-scoped roles are not attached to the user directly: they hang off
    LangSmithWorkspaceMembership, which also records which workspace the role applies in.
    """

    target_node_label: str = "LangSmithRole"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("org_role_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_ROLE"
    properties: LangSmithUserToOrgRoleRelProperties = (
        LangSmithUserToOrgRoleRelProperties()
    )


@dataclass(frozen=True)
class LangSmithUserToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:LangSmithUser)-[:MEMBER_OF]->(:LangSmithWorkspace)
class LangSmithUserToWorkspaceRel(CartographyRelSchema):
    """A user is a member of a workspace. The role held there is on the membership node."""

    target_node_label: str = "LangSmithWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("tenant_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF"
    properties: LangSmithUserToWorkspaceRelProperties = (
        LangSmithUserToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class LangSmithUserSchema(CartographyNodeSchema):
    """A LangSmith user account, keyed on the stable ls_user_id."""

    label: str = "LangSmithUser"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [USER_ACCOUNT]
    )  # UserAccount label is used for ontology mapping
    properties: LangSmithUserNodeProperties = LangSmithUserNodeProperties()
    sub_resource_relationship: LangSmithUserToOrganizationRel = (
        LangSmithUserToOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            LangSmithUserToOrgRoleRel(),
            LangSmithUserToWorkspaceRel(),
        ],
    )
