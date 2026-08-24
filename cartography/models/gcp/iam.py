import logging
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
from cartography.models.extra_labels import GCP_PRINCIPAL
from cartography.models.ontology.labels import PERMISSION_ROLE
from cartography.models.ontology.labels import SERVICE_ACCOUNT

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class GCPServiceAccountNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        extra_index=True,
        description="Stable numeric uniqueId used as the service account graph ID.",
    )
    email: PropertyRef = PropertyRef(
        "email",
        extra_index=True,
        description="The email address associated with the service account.",
    )
    display_name: PropertyRef = PropertyRef(
        "displayName", description="Human-readable name shown for this resource."
    )
    oauth2_client_id: PropertyRef = PropertyRef(
        "oauth2ClientId",
        description="OAuth 2.0 client ID assigned to the service account.",
    )
    unique_id: PropertyRef = PropertyRef(
        "uniqueId",
        description="Stable numeric Google-generated service account ID used as the graph identifier.",
    )
    disabled: PropertyRef = PropertyRef(
        "disabled",
        description="A boolean indicating if the service account is disabled.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    project_id: PropertyRef = PropertyRef(
        "projectId",
        set_in_kwargs=True,
        description="Google Cloud project that owns this resource.",
    )


@dataclass(frozen=True)
class GCPIAMToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:GCPServiceAccount)<-[:RESOURCE]-(:GCPProject)
class GCPPrincipalToProjectRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("projectId", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPIAMToProjectRelProperties = GCPIAMToProjectRelProperties()


@dataclass(frozen=True)
class GCPServiceAccountSchema(CartographyNodeSchema):
    """Representation of a GCP [Service Account](https://cloud.google.com/iam/docs/reference/rest/v1/projects.serviceAccounts)."""

    label: str = "GCPServiceAccount"
    properties: GCPServiceAccountNodeProperties = GCPServiceAccountNodeProperties()
    sub_resource_relationship: GCPPrincipalToProjectRel = GCPPrincipalToProjectRel()
    # Service accounts are principals; add shared label for cross-module queries
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [GCP_PRINCIPAL, SERVICE_ACCOUNT]
    )


# =============================================================================
# Organization-level roles (predefined/basic roles and custom org roles)
# =============================================================================


@dataclass(frozen=True)
class GCPOrgRoleNodeProperties(CartographyNodeProperties):
    """Properties for organization-level roles (predefined and custom org roles)."""

    id: PropertyRef = PropertyRef(
        "name",
        extra_index=True,
        description="The unique identifier for the role (same as name).",
    )
    name: PropertyRef = PropertyRef(
        "name",
        extra_index=True,
        description="The name of the role (e.g., `roles/editor`, `organizations/123/roles/custom`, `projects/abc/roles/custom`).",
    )
    title: PropertyRef = PropertyRef(
        "title", description="The human-readable title of the role."
    )
    description: PropertyRef = PropertyRef(
        "description", description="A description of the role."
    )
    deleted: PropertyRef = PropertyRef(
        "deleted", description="A boolean indicating if the role is deleted."
    )
    etag: PropertyRef = PropertyRef(
        "etag", description="The ETag of the role for optimistic concurrency control."
    )
    permissions: PropertyRef = PropertyRef(
        "includedPermissions", description="A list of permissions included in the role."
    )
    role_type: PropertyRef = PropertyRef(
        "roleType", description="IAM role category, such as predefined or custom."
    )  # BASIC, PREDEFINED, or CUSTOM
    scope: PropertyRef = PropertyRef(
        "scope",
        description="The scope of the role: `GLOBAL` (predefined/basic), `ORGANIZATION` (custom org), or `PROJECT` (custom project).",
    )  # GLOBAL or ORGANIZATION
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    organization_id: PropertyRef = PropertyRef(
        "organizationId",
        set_in_kwargs=True,
        description="Google Cloud organization that owns this resource.",
    )


@dataclass(frozen=True)
class GCPOrgRoleToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPOrgRoleToOrganizationRel(CartographyRelSchema):
    """Relationship connecting organization-level GCPRole to GCPOrganization."""

    target_node_label: str = "GCPOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("organizationId", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPOrgRoleToOrganizationRelProperties = (
        GCPOrgRoleToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class GCPOrgRoleSchema(CartographyNodeSchema):
    """A predefined or organization-level Google Cloud IAM role."""

    label: str = "GCPRole"
    properties: GCPOrgRoleNodeProperties = GCPOrgRoleNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([PERMISSION_ROLE])
    sub_resource_relationship: GCPOrgRoleToOrganizationRel = (
        GCPOrgRoleToOrganizationRel()
    )


# =============================================================================
# Standalone predefined roles (global roles synced without organization context)
# =============================================================================


@dataclass(frozen=True)
class GCPPredefinedRoleNodeProperties(CartographyNodeProperties):
    """
    Properties for global predefined/basic roles synced without organization context.

    Same shape as GCPOrgRoleNodeProperties but without the ``organization_id`` sub-resource
    key: predefined roles (roles/*) are global and not owned by any organization.
    """

    id: PropertyRef = PropertyRef("name", extra_index=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    title: PropertyRef = PropertyRef("title")
    description: PropertyRef = PropertyRef("description")
    deleted: PropertyRef = PropertyRef("deleted")
    etag: PropertyRef = PropertyRef("etag")
    permissions: PropertyRef = PropertyRef("includedPermissions")
    role_type: PropertyRef = PropertyRef("roleType")  # BASIC or PREDEFINED
    scope: PropertyRef = PropertyRef("scope")  # GLOBAL
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPStandalonePredefinedRoleSchema(CartographyNodeSchema):
    """
    Global predefined/basic GCP IAM roles (roles/*) synced in the standalone
    (``--gcp-project-ids``) path, where there is no organization to own them.

    Identical to GCPOrgRoleSchema in label (``GCPRole``) and permission modeling, so that
    the ``(:GCPPolicyBinding)-[:GRANTS_ROLE]->(:GCPRole)`` matchlink resolves for bindings
    that reference predefined roles. It differs in two ways:

    - No ``sub_resource_relationship``: predefined roles are global, not owned by an org.
    - ``scoped_cleanup`` is False: the standalone path intentionally runs no cleanup for
      these nodes. A global GCPRole cleanup would delete role nodes synced by the
      organization-based path (both paths MERGE on the role name). This mirrors how
      Cartography treats other global, cross-scope reference nodes — e.g. AWS managed
      policies (cartography/intel/aws/iam.py::cleanup_iam) are also not node-cleaned
      because they are shared and deleting them for one scope would remove them for
      another. The flag exists only to satisfy the data model's rule that
      ``sub_resource_relationship`` may be None only when ``scoped_cleanup`` is False.
    """

    label: str = "GCPRole"
    properties: GCPPredefinedRoleNodeProperties = GCPPredefinedRoleNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["PermissionRole"])
    sub_resource_relationship: None = None
    scoped_cleanup: bool = False


# =============================================================================
# Project-level roles (custom project roles only)
# =============================================================================


@dataclass(frozen=True)
class GCPProjectRoleNodeProperties(CartographyNodeProperties):
    """Properties for project-level custom roles."""

    id: PropertyRef = PropertyRef(
        "name",
        extra_index=True,
        description="The unique identifier for the role (same as name).",
    )
    name: PropertyRef = PropertyRef(
        "name",
        extra_index=True,
        description="The name of the role (e.g., `roles/editor`, `organizations/123/roles/custom`, `projects/abc/roles/custom`).",
    )
    title: PropertyRef = PropertyRef(
        "title", description="The human-readable title of the role."
    )
    description: PropertyRef = PropertyRef(
        "description", description="A description of the role."
    )
    deleted: PropertyRef = PropertyRef(
        "deleted", description="A boolean indicating if the role is deleted."
    )
    etag: PropertyRef = PropertyRef(
        "etag", description="The ETag of the role for optimistic concurrency control."
    )
    permissions: PropertyRef = PropertyRef(
        "includedPermissions", description="A list of permissions included in the role."
    )
    role_type: PropertyRef = PropertyRef(
        "roleType", description="IAM role category, such as predefined or custom."
    )  # Always CUSTOM for project roles
    scope: PropertyRef = PropertyRef(
        "scope",
        description="The scope of the role: `GLOBAL` (predefined/basic), `ORGANIZATION` (custom org), or `PROJECT` (custom project).",
    )  # Always PROJECT
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    project_id: PropertyRef = PropertyRef(
        "projectId",
        set_in_kwargs=True,
        description="Google Cloud project that owns this resource.",
    )


@dataclass(frozen=True)
class GCPProjectRoleToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPProjectRoleToProjectRel(CartographyRelSchema):
    """Relationship connecting project-level GCPRole to GCPProject."""

    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("projectId", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPProjectRoleToProjectRelProperties = (
        GCPProjectRoleToProjectRelProperties()
    )


@dataclass(frozen=True)
class GCPProjectRoleSchema(CartographyNodeSchema):
    """A custom Google Cloud IAM role defined in a single project."""

    label: str = "GCPRole"
    properties: GCPProjectRoleNodeProperties = GCPProjectRoleNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([PERMISSION_ROLE])
    sub_resource_relationship: GCPProjectRoleToProjectRel = GCPProjectRoleToProjectRel()
