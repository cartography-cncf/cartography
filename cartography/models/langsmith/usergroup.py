from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_source_node_matcher
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import SourceNodeMatcher
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.ontology.labels import USER_GROUP


@dataclass(frozen=True)
class LangSmithUserGroupNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="User group UUID.")
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="User group name."
    )
    description: PropertyRef = PropertyRef(
        "description", description="Human-readable description of the user group."
    )
    workspace_id: PropertyRef = PropertyRef(
        "workspace_id",
        description=(
            "UUID of the workspace that a workspace-scoped user group belongs to. Empty "
            "for an organization-wide user group."
        ),
    )
    parent_user_group_id: PropertyRef = PropertyRef(
        "parent_user_group_id",
        description=(
            "UUID of the organization-wide user group that a workspace-scoped user group "
            "extends. Empty for an organization-wide user group."
        ),
    )
    idp_group_name: PropertyRef = PropertyRef(
        "idp_group_name",
        extra_index=True,
        description=(
            "Name of the identity provider group, from SCIM or SSO group sync, that the "
            "user group is linked to."
        ),
    )
    idp_sync_enabled: PropertyRef = PropertyRef(
        "idp_sync_enabled",
        description=(
            "True if LangSmith sets the user group's members from its identity provider "
            "group."
        ),
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="When the user group was created."
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="When the user group was last updated."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class LangSmithUserGroupToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:LangSmithOrganization)-[:RESOURCE]->(:LangSmithUserGroup)
class LangSmithUserGroupToOrganizationRel(CartographyRelSchema):
    """Links an organization to one of its user groups."""

    target_node_label: str = "LangSmithOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: LangSmithUserGroupToOrganizationRelProperties = (
        LangSmithUserGroupToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class LangSmithUserGroupToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:LangSmithUserGroup)-[:IN_WORKSPACE]->(:LangSmithWorkspace)
class LangSmithUserGroupToWorkspaceRel(CartographyRelSchema):
    """Links a workspace-scoped user group to the workspace it belongs to."""

    target_node_label: str = "LangSmithWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("workspace_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "IN_WORKSPACE"
    properties: LangSmithUserGroupToWorkspaceRelProperties = (
        LangSmithUserGroupToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class LangSmithUserGroupToParentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:LangSmithUserGroup)-[:EXTENDS]->(:LangSmithUserGroup)
class LangSmithUserGroupToParentRel(CartographyRelSchema):
    """
    A workspace-scoped user group extends an organization-wide user group in one
    workspace. Its members get only its own access policies, not the parent's role.
    """

    target_node_label: str = "LangSmithUserGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("parent_user_group_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "EXTENDS"
    properties: LangSmithUserGroupToParentRelProperties = (
        LangSmithUserGroupToParentRelProperties()
    )


@dataclass(frozen=True)
class LangSmithUserGroupToUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:LangSmithUser)-[:MEMBER_OF]->(:LangSmithUserGroup)
class LangSmithUserGroupToUserRel(CartographyRelSchema):
    """Links a user to a user group they belong to."""

    target_node_label: str = "LangSmithUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("member_ls_user_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "MEMBER_OF"
    properties: LangSmithUserGroupToUserRelProperties = (
        LangSmithUserGroupToUserRelProperties()
    )


@dataclass(frozen=True)
class LangSmithUserGroupSchema(CartographyNodeSchema):
    """
    A user group: a set of organization members that gets a role in each workspace it
    is granted into, and the access policies attached to it.

    A user's permissions in a workspace combine their own role with the role of each user
    group they belong to, and a deny policy from any of them blocks access. A user group
    grants its role only to members who also belong to the workspace.

    Granting an organization-wide user group into a workspace creates a workspace-scoped
    user group there, which EXTENDS the organization-wide one. A workspace admin can add
    workspace-only members and policies to it.
    """

    label: str = "LangSmithUserGroup"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([USER_GROUP])
    properties: LangSmithUserGroupNodeProperties = LangSmithUserGroupNodeProperties()
    sub_resource_relationship: LangSmithUserGroupToOrganizationRel = (
        LangSmithUserGroupToOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            LangSmithUserGroupToWorkspaceRel(),
            LangSmithUserGroupToParentRel(),
            LangSmithUserGroupToUserRel(),
        ],
    )


@dataclass(frozen=True)
class LangSmithUserGroupGrantNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Synthetic identifier of the form <user_group_id>|<workspace_id>.",
    )
    user_group_id: PropertyRef = PropertyRef(
        "user_group_id", description="UUID of the user group."
    )
    workspace_id: PropertyRef = PropertyRef(
        "workspace_id", extra_index=True, description="UUID of the workspace."
    )
    role_name: PropertyRef = PropertyRef(
        "role_name",
        description="Display name of the role that the user group holds in the workspace.",
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="When the user group was granted into the workspace."
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="When the grant's role was last changed."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class LangSmithUserGroupGrantToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:LangSmithOrganization)-[:RESOURCE]->(:LangSmithUserGroupGrant)
class LangSmithUserGroupGrantToOrganizationRel(CartographyRelSchema):
    """Links an organization to a user group's grant into one of its workspaces."""

    target_node_label: str = "LangSmithOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: LangSmithUserGroupGrantToOrganizationRelProperties = (
        LangSmithUserGroupGrantToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class LangSmithUserGroupGrantToUserGroupRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:LangSmithUserGroup)-[:HAS_GRANT]->(:LangSmithUserGroupGrant)
class LangSmithUserGroupGrantToUserGroupRel(CartographyRelSchema):
    """Links a user group to its grant into one workspace."""

    target_node_label: str = "LangSmithUserGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("user_group_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_GRANT"
    properties: LangSmithUserGroupGrantToUserGroupRelProperties = (
        LangSmithUserGroupGrantToUserGroupRelProperties()
    )


@dataclass(frozen=True)
class LangSmithUserGroupGrantToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:LangSmithUserGroupGrant)-[:IN_WORKSPACE]->(:LangSmithWorkspace)
class LangSmithUserGroupGrantToWorkspaceRel(CartographyRelSchema):
    """Links a grant to the workspace it gives the user group's members a role in."""

    target_node_label: str = "LangSmithWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("workspace_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "IN_WORKSPACE"
    properties: LangSmithUserGroupGrantToWorkspaceRelProperties = (
        LangSmithUserGroupGrantToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class LangSmithUserGroupGrantToRoleRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:LangSmithUserGroupGrant)-[:HAS_ROLE]->(:LangSmithRole)
class LangSmithUserGroupGrantToRoleRel(CartographyRelSchema):
    """Links a grant to the role it gives the user group's members in the workspace."""

    target_node_label: str = "LangSmithRole"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("role_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_ROLE"
    properties: LangSmithUserGroupGrantToRoleRelProperties = (
        LangSmithUserGroupGrantToRoleRelProperties()
    )


@dataclass(frozen=True)
class LangSmithUserGroupGrantSchema(CartographyNodeSchema):
    """
    A user group's access to one workspace, together with the role its members get there.

    Modeled as a node for the same reason as LangSmithWorkspaceMembership: the grant is a
    (user group, workspace, role) triple, and roles can be organization-defined. Only
    organization-wide user groups have grants. A workspace-scoped user group's access to
    its workspace gives no permissions, and LangSmith doesn't list it.
    """

    label: str = "LangSmithUserGroupGrant"
    properties: LangSmithUserGroupGrantNodeProperties = (
        LangSmithUserGroupGrantNodeProperties()
    )
    sub_resource_relationship: LangSmithUserGroupGrantToOrganizationRel = (
        LangSmithUserGroupGrantToOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            LangSmithUserGroupGrantToUserGroupRel(),
            LangSmithUserGroupGrantToWorkspaceRel(),
            LangSmithUserGroupGrantToRoleRel(),
        ],
    )


@dataclass(frozen=True)
class LangSmithAccessPolicyToUserGroupRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)
    all_workspaces: PropertyRef = PropertyRef(
        "all_workspaces",
        description=(
            "True if the policy applies in every workspace that the user group can access."
        ),
    )
    workspace_ids: PropertyRef = PropertyRef(
        "workspace_ids",
        description=(
            "Workspaces that the policy is limited to, when it's attached for specific "
            "workspaces only."
        ),
    )


# A policy can be attached to the same user group for all workspaces and for specific
# workspaces at once. A matchlink carries those scopes as relationship properties.
@dataclass(frozen=True)
# (:LangSmithAccessPolicy)-[:ATTACHED_TO]->(:LangSmithUserGroup)
class LangSmithAccessPolicyToUserGroupRel(CartographyRelSchema):
    """An access policy applies to a user group's members."""

    source_node_label: str = "LangSmithAccessPolicy"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("access_policy_id")},
    )
    target_node_label: str = "LangSmithUserGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("user_group_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ATTACHED_TO"
    properties: LangSmithAccessPolicyToUserGroupRelProperties = (
        LangSmithAccessPolicyToUserGroupRelProperties()
    )
