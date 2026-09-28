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
from cartography.models.ontology.labels import PERMISSION_ROLE


@dataclass(frozen=True)
class ModalWorkspaceRoleNodeProperties(CartographyNodeProperties):
    # Modal has no role object, so the id is synthesised as "<workspace_id>/<role>".
    id: PropertyRef = PropertyRef(
        "id", description="Synthesised as `<workspace_id>/<role>`."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    # One of member, manager, owner (normalised from the MEMBER_ROLE_* enum).
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="`member`, `manager` or `owner`."
    )
    scope: PropertyRef = PropertyRef("scope", description="Always `workspace`.")


@dataclass(frozen=True)
class ModalWorkspaceRoleToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ModalWorkspace)-[:RESOURCE]->(:ModalWorkspaceRole)
class ModalWorkspaceRoleToWorkspaceRel(CartographyRelSchema):
    target_node_label: str = "ModalWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKSPACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ModalWorkspaceRoleToWorkspaceRelProperties = (
        ModalWorkspaceRoleToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
# Modal's workspace-level roles are a fixed builtin set rather than API objects. They
# are materialised as PermissionRole nodes (instead of a plain property on the member)
# because ONTOLOGY_REL_CONSTRAINTS already blesses UserAccount -> PermissionRole as
# HAS_ROLE, so modelling them this way puts Modal RBAC into cross-provider rules.
class ModalWorkspaceRoleSchema(CartographyNodeSchema):
    """Represents one of Modal's builtin workspace roles (`member`, `manager`, `owner`). Modal has no role API object, so these nodes are derived from the role enum and their id is synthesised as `<workspace_id>/<role>`. Modelling roles as nodes rather than as a property on the member is what lets Modal RBAC participate in cross-provider `HAS_ROLE` rules."""

    label: str = "ModalWorkspaceRole"
    properties: ModalWorkspaceRoleNodeProperties = ModalWorkspaceRoleNodeProperties()
    sub_resource_relationship: ModalWorkspaceRoleToWorkspaceRel = (
        ModalWorkspaceRoleToWorkspaceRel()
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([PERMISSION_ROLE])
