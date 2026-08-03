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
from cartography.models.ontology.labels import USER_GROUP


@dataclass(frozen=True)
class AnthropicRbacRoleNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Anthropic RBAC role ID.")
    name: PropertyRef = PropertyRef("name", description="RBAC role name.")
    created_at: PropertyRef = PropertyRef(
        "created_at",
        description="RFC 3339 timestamp when the role was created.",
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at",
        description="RFC 3339 timestamp when the role was last updated.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AnthropicRbacRoleToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AnthropicOrganization)-[:RESOURCE]->(:AnthropicRbacRole)
class AnthropicRbacRoleToOrganizationRel(CartographyRelSchema):
    """The organization defines the RBAC role."""

    target_node_label: str = "AnthropicOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AnthropicRbacRoleToOrganizationRelProperties = (
        AnthropicRbacRoleToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class AnthropicRbacRoleSchema(CartographyNodeSchema):
    """A custom role in a Claude Enterprise organization."""

    label: str = "AnthropicRbacRole"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([PERMISSION_ROLE])
    properties: AnthropicRbacRoleNodeProperties = AnthropicRbacRoleNodeProperties()
    sub_resource_relationship: AnthropicRbacRoleToOrganizationRel = (
        AnthropicRbacRoleToOrganizationRel()
    )


@dataclass(frozen=True)
class AnthropicRbacRolePermissionNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description=(
            "Synthesised from the role, action and resource. The API returns no "
            "identifier for a permission."
        ),
    )
    action: PropertyRef = PropertyRef(
        "action",
        description=(
            "Action the permission grants on the resource. Free-form: the API "
            "declares no enumeration. The blanket values capability_access_all and "
            "capability_access_all_ga each stand for every product-feature "
            "entitlement they cover, so reading a role's grants literally will "
            "under-report its effective access."
        ),
    )
    resource_type: PropertyRef = PropertyRef(
        "resource.type",
        description=(
            "Kind of resource granted on: organization, connector, connector_tool, "
            "connector_scope, or all_connectors."
        ),
    )
    resource_organization_id: PropertyRef = PropertyRef(
        "resource.organization_id",
        description="Organization granted on, for organization-type resources.",
    )
    resource_connector_id: PropertyRef = PropertyRef(
        "resource.connector_id",
        description="Connector granted on, for connector-type resources.",
    )
    resource_tool_name: PropertyRef = PropertyRef(
        "resource.tool_name",
        description=(
            "Tool granted on. Names containing characters outside [a-zA-Z0-9_-] are "
            "server-encoded to a stable {prefix}_{32-hex} form the original name "
            "cannot be recovered from; treat this as an opaque identifier."
        ),
    )
    resource_scope: PropertyRef = PropertyRef(
        "resource.scope",
        description=(
            "OAuth scope granted. Scopes routinely contain ':' and '/', so most "
            "arrive in the server-encoded opaque form."
        ),
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AnthropicRbacRolePermissionToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AnthropicOrganization)-[:RESOURCE]->(:AnthropicRbacRolePermission)
class AnthropicRbacRolePermissionToOrganizationRel(CartographyRelSchema):
    """The organization the permission belongs to."""

    target_node_label: str = "AnthropicOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AnthropicRbacRolePermissionToOrganizationRelProperties = (
        AnthropicRbacRolePermissionToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class AnthropicRbacRolePermissionToRoleRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AnthropicRbacRole)-[:GRANTS]->(:AnthropicRbacRolePermission)
class AnthropicRbacRolePermissionToRoleRel(CartographyRelSchema):
    """The role grants this permission."""

    target_node_label: str = "AnthropicRbacRole"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("role_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "GRANTS"
    properties: AnthropicRbacRolePermissionToRoleRelProperties = (
        AnthropicRbacRolePermissionToRoleRelProperties()
    )


@dataclass(frozen=True)
class AnthropicRbacRolePermissionSchema(CartographyNodeSchema):
    """A single action-on-resource grant carried by an RBAC role."""

    label: str = "AnthropicRbacRolePermission"
    properties: AnthropicRbacRolePermissionNodeProperties = (
        AnthropicRbacRolePermissionNodeProperties()
    )
    sub_resource_relationship: AnthropicRbacRolePermissionToOrganizationRel = (
        AnthropicRbacRolePermissionToOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AnthropicRbacRolePermissionToRoleRel(),
        ],
    )


@dataclass(frozen=True)
class AnthropicRbacGroupNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Anthropic RBAC group ID.")
    name: PropertyRef = PropertyRef("name", description="RBAC group name.")
    source_type: PropertyRef = PropertyRef(
        "source_type",
        description=(
            "How the group is provisioned: direct, or scim when it is synced from an "
            "external directory."
        ),
    )
    created_at: PropertyRef = PropertyRef(
        "created_at",
        description="RFC 3339 timestamp when the group was created.",
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at",
        description="RFC 3339 timestamp when the group was last updated.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AnthropicRbacGroupToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AnthropicOrganization)-[:RESOURCE]->(:AnthropicRbacGroup)
class AnthropicRbacGroupToOrganizationRel(CartographyRelSchema):
    """The organization contains the RBAC group."""

    target_node_label: str = "AnthropicOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AnthropicRbacGroupToOrganizationRelProperties = (
        AnthropicRbacGroupToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class AnthropicRbacGroupToRoleRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AnthropicRbacGroup)-[:HAS_ROLE]->(:AnthropicRbacRole)
class AnthropicRbacGroupToRoleRel(CartographyRelSchema):
    """The group holds the role; its members inherit the role's permissions."""

    target_node_label: str = "AnthropicRbacRole"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("roles", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_ROLE"
    properties: AnthropicRbacGroupToRoleRelProperties = (
        AnthropicRbacGroupToRoleRelProperties()
    )


@dataclass(frozen=True)
class AnthropicRbacGroupToUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AnthropicUser)-[:MEMBER_OF]->(:AnthropicRbacGroup)
class AnthropicRbacGroupToUserRel(CartographyRelSchema):
    """A user is a member of the group."""

    target_node_label: str = "AnthropicUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("members", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "MEMBER_OF"
    properties: AnthropicRbacGroupToUserRelProperties = (
        AnthropicRbacGroupToUserRelProperties()
    )


@dataclass(frozen=True)
class AnthropicRbacGroupSchema(CartographyNodeSchema):
    """A group in a Claude Enterprise organization, holding roles its members inherit."""

    label: str = "AnthropicRbacGroup"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([USER_GROUP])
    properties: AnthropicRbacGroupNodeProperties = AnthropicRbacGroupNodeProperties()
    sub_resource_relationship: AnthropicRbacGroupToOrganizationRel = (
        AnthropicRbacGroupToOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AnthropicRbacGroupToRoleRel(),
            AnthropicRbacGroupToUserRel(),
        ],
    )
