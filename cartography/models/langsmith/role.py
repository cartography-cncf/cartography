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
from cartography.models.ontology.labels import PERMISSION_ROLE


@dataclass(frozen=True)
class LangSmithRoleNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Role UUID.")
    name: PropertyRef = PropertyRef(
        "display_name",
        extra_index=True,
        description=(
            "Role display name. Prefer this over system_name: every custom role is stored "
            "with the system name CUSTOM, so only the display name distinguishes them."
        ),
    )
    system_name: PropertyRef = PropertyRef(
        "name",
        description=(
            "Internal role name, for example ORGANIZATION_ADMIN or WORKSPACE_VIEWER. "
            "Always CUSTOM for user-defined roles."
        ),
    )
    description: PropertyRef = PropertyRef(
        "description", description="Human-readable description of the role."
    )
    access_scope: PropertyRef = PropertyRef(
        "access_scope",
        description="Whether the role applies at organization or workspace scope.",
    )
    is_custom: PropertyRef = PropertyRef(
        "is_custom",
        description=(
            "True if this is a user-defined role rather than a LangSmith built-in. "
            "Derived from the presence of an owning organization_id."
        ),
    )
    is_restricted: PropertyRef = PropertyRef(
        "is_restricted",
        description="True if the organization has applied a restriction to this role.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class LangSmithRoleToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:LangSmithOrganization)-[:RESOURCE]->(:LangSmithRole)
class LangSmithRoleToOrganizationRel(CartographyRelSchema):
    """Links an organization to a role available within it."""

    target_node_label: str = "LangSmithOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: LangSmithRoleToOrganizationRelProperties = (
        LangSmithRoleToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class LangSmithRoleToPermissionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:LangSmithRole)-[:GRANTS]->(:LangSmithPermission)
class LangSmithRoleToPermissionRel(CartographyRelSchema):
    """A role grants a permission."""

    target_node_label: str = "LangSmithPermission"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("permissions", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "GRANTS"
    properties: LangSmithRoleToPermissionRelProperties = (
        LangSmithRoleToPermissionRelProperties()
    )


@dataclass(frozen=True)
class LangSmithRoleSchema(CartographyNodeSchema):
    """A LangSmith RBAC role, either a built-in system role or an organization's custom role."""

    label: str = "LangSmithRole"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [PERMISSION_ROLE]
    )  # PermissionRole label is used for ontology mapping
    properties: LangSmithRoleNodeProperties = LangSmithRoleNodeProperties()
    sub_resource_relationship: LangSmithRoleToOrganizationRel = (
        LangSmithRoleToOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            LangSmithRoleToPermissionRel(),
        ],
    )
