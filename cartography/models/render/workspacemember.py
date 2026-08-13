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
class RenderWorkspaceMemberNodeProperties(CartographyNodeProperties):
    # Scoped per-workspace-membership (`<owner id>:<user id>`), not bare userId. A
    # Render user id is shared across every workspace they belong to, but this
    # module's cleanup is scoped per-workspace like every other resource here; merging
    # on bare userId would let one workspace's cleanup pass delete a person's node
    # while they are still a valid member of another workspace the same key can see.
    # See RenderWorkspaceMemberToTenantRel's docstring.
    id: PropertyRef = PropertyRef(
        "id", description="Synthetic id: `<workspace id>:<user id>`."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    user_id: PropertyRef = PropertyRef(
        "userId",
        extra_index=True,
        description="Render user id, shared across workspaces.",
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Display name of the member."
    )
    email: PropertyRef = PropertyRef(
        "email", extra_index=True, description="Email address of the member."
    )
    owner_id: PropertyRef = PropertyRef(
        "ownerId", description="ID of the workspace this membership belongs to."
    )
    status: PropertyRef = PropertyRef(
        "status", description="Membership status: `active` or `inactive`."
    )
    role: PropertyRef = PropertyRef(
        "role",
        extra_index=True,
        description=(
            "Workspace role: ADMIN, DEVELOPER, WORKSPACE_CONTRIBUTOR, "
            "WORKSPACE_BILLING, or WORKSPACE_VIEWER."
        ),
    )
    mfa_enabled: PropertyRef = PropertyRef(
        "mfaEnabled",
        extra_index=True,
        description="Whether the member has multi-factor authentication enabled.",
    )


@dataclass(frozen=True)
class RenderWorkspaceMemberToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:RenderTenant)-[:RESOURCE]->(:RenderWorkspaceMember)
class RenderWorkspaceMemberToTenantRel(CartographyRelSchema):
    """Connects a Render workspace to a member of it."""

    target_node_label: str = "RenderTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("OWNER_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: RenderWorkspaceMemberToTenantRelProperties = (
        RenderWorkspaceMemberToTenantRelProperties()
    )


@dataclass(frozen=True)
class RenderWorkspaceMemberSchema(CartographyNodeSchema):
    """A member of a Render workspace: an identity with a role in that workspace."""

    label: str = "RenderWorkspaceMember"
    properties: RenderWorkspaceMemberNodeProperties = (
        RenderWorkspaceMemberNodeProperties()
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([USER_ACCOUNT])
    sub_resource_relationship: RenderWorkspaceMemberToTenantRel = (
        RenderWorkspaceMemberToTenantRel()
    )
