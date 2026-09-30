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
class LangSmithWorkspaceMembershipNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Synthetic identifier of the form <ls_user_id>|<workspace_id>.",
    )
    identity_id: PropertyRef = PropertyRef(
        "identity_id",
        description="UUID of the workspace-scoped identity row backing this membership.",
    )
    ls_user_id: PropertyRef = PropertyRef(
        "ls_user_id",
        extra_index=True,
        description="Stable LangSmith user ID of the member.",
    )
    workspace_id: PropertyRef = PropertyRef(
        "workspace_id", extra_index=True, description="UUID of the workspace."
    )
    email: PropertyRef = PropertyRef(
        "email",
        description="Email address of the member, denormalized for convenience.",
    )
    role_name: PropertyRef = PropertyRef(
        "role_name", description="Display name of the role held in this workspace."
    )
    is_disabled: PropertyRef = PropertyRef(
        "is_disabled", description="True if the member's identity is deactivated."
    )
    is_pending: PropertyRef = PropertyRef(
        "is_pending",
        description="True if this is an outstanding workspace invitation rather than an accepted membership.",
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Timestamp when the membership was created."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class LangSmithWorkspaceMembershipToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:LangSmithOrganization)-[:RESOURCE]->(:LangSmithWorkspaceMembership)
class LangSmithWorkspaceMembershipToOrganizationRel(CartographyRelSchema):
    """Links an organization to a workspace membership within it."""

    target_node_label: str = "LangSmithOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: LangSmithWorkspaceMembershipToOrganizationRelProperties = (
        LangSmithWorkspaceMembershipToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class LangSmithWorkspaceMembershipToUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:LangSmithUser)-[:HAS_MEMBERSHIP]->(:LangSmithWorkspaceMembership)
class LangSmithWorkspaceMembershipToUserRel(CartographyRelSchema):
    """Links a user to one of their workspace memberships."""

    target_node_label: str = "LangSmithUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ls_user_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_MEMBERSHIP"
    properties: LangSmithWorkspaceMembershipToUserRelProperties = (
        LangSmithWorkspaceMembershipToUserRelProperties()
    )


@dataclass(frozen=True)
class LangSmithWorkspaceMembershipToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:LangSmithWorkspaceMembership)-[:IN_WORKSPACE]->(:LangSmithWorkspace)
class LangSmithWorkspaceMembershipToWorkspaceRel(CartographyRelSchema):
    """Links a membership to the workspace it grants access to."""

    target_node_label: str = "LangSmithWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("workspace_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "IN_WORKSPACE"
    properties: LangSmithWorkspaceMembershipToWorkspaceRelProperties = (
        LangSmithWorkspaceMembershipToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class LangSmithWorkspaceMembershipToRoleRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:LangSmithWorkspaceMembership)-[:HAS_ROLE]->(:LangSmithRole)
class LangSmithWorkspaceMembershipToRoleRel(CartographyRelSchema):
    """Links a membership to the role it confers in that workspace."""

    target_node_label: str = "LangSmithRole"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("role_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_ROLE"
    properties: LangSmithWorkspaceMembershipToRoleRelProperties = (
        LangSmithWorkspaceMembershipToRoleRelProperties()
    )


@dataclass(frozen=True)
class LangSmithWorkspaceMembershipSchema(CartographyNodeSchema):
    """
    A user's membership of a single workspace, together with the role they hold there.

    This is modelled as a node rather than a relationship because role assignment is a
    (user, workspace, role) triple and LangSmith supports organization-defined custom roles,
    so the role cannot be encoded in a fixed set of relationship labels.
    """

    label: str = "LangSmithWorkspaceMembership"
    properties: LangSmithWorkspaceMembershipNodeProperties = (
        LangSmithWorkspaceMembershipNodeProperties()
    )
    sub_resource_relationship: LangSmithWorkspaceMembershipToOrganizationRel = (
        LangSmithWorkspaceMembershipToOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            LangSmithWorkspaceMembershipToUserRel(),
            LangSmithWorkspaceMembershipToWorkspaceRel(),
            LangSmithWorkspaceMembershipToRoleRel(),
        ],
    )
