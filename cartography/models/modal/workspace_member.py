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
class ModalWorkspaceMemberNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    # Carried as a property, not just as the RESOURCE edge, so best-effort CREATED_BY joins
    # from other Modal nodes can be constrained to this workspace. Without it, a graph holding
    # two Modal workspaces would attribute creation to every member sharing a display name.
    workspace_id: PropertyRef = PropertyRef("WORKSPACE_ID", set_in_kwargs=True)
    member_id: PropertyRef = PropertyRef("member_id")
    email: PropertyRef = PropertyRef("email", extra_index=True)
    display_name: PropertyRef = PropertyRef("display_name", extra_index=True)
    member_role: PropertyRef = PropertyRef("member_role", extra_index=True)
    # GITHUB, OKTA or GOOGLE_OAUTH. A non-SSO provider in an SSO-managed workspace is
    # a finding, so this is indexed.
    identity_provider_type: PropertyRef = PropertyRef(
        "identity_provider_type", extra_index=True
    )
    idp_external_id: PropertyRef = PropertyRef("idp_external_id")
    avatar_url: PropertyRef = PropertyRef("avatar_url")
    joined_at: PropertyRef = PropertyRef("joined_at")
    last_active_at: PropertyRef = PropertyRef("last_active_at")
    deleted_at: PropertyRef = PropertyRef("deleted_at")


@dataclass(frozen=True)
class ModalWorkspaceMemberToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ModalWorkspace)-[:RESOURCE]->(:ModalWorkspaceMember)
class ModalWorkspaceMemberToWorkspaceRel(CartographyRelSchema):
    target_node_label: str = "ModalWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKSPACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ModalWorkspaceMemberToWorkspaceRelProperties = (
        ModalWorkspaceMemberToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class ModalWorkspaceMemberToWorkspaceRoleRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ModalWorkspaceMember)-[:HAS_ROLE]->(:ModalWorkspaceRole)
# workspace_role_id is computed in transform as "<workspace_id>/<role>".
class ModalWorkspaceMemberToWorkspaceRoleRel(CartographyRelSchema):
    target_node_label: str = "ModalWorkspaceRole"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("workspace_role_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_ROLE"
    properties: ModalWorkspaceMemberToWorkspaceRoleRelProperties = (
        ModalWorkspaceMemberToWorkspaceRoleRelProperties()
    )


@dataclass(frozen=True)
class ModalWorkspaceMemberSchema(CartographyNodeSchema):
    label: str = "ModalWorkspaceMember"
    properties: ModalWorkspaceMemberNodeProperties = (
        ModalWorkspaceMemberNodeProperties()
    )
    sub_resource_relationship: ModalWorkspaceMemberToWorkspaceRel = (
        ModalWorkspaceMemberToWorkspaceRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [ModalWorkspaceMemberToWorkspaceRoleRel()],
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([USER_ACCOUNT])
