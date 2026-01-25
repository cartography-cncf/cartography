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

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class GCPServiceAccountNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", extra_index=True)
    email: PropertyRef = PropertyRef("email", extra_index=True)
    display_name: PropertyRef = PropertyRef("displayName")
    oauth2_client_id: PropertyRef = PropertyRef("oauth2ClientId")
    unique_id: PropertyRef = PropertyRef("uniqueId")
    disabled: PropertyRef = PropertyRef("disabled")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    project_id: PropertyRef = PropertyRef("projectId", set_in_kwargs=True)


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
    label: str = "GCPServiceAccount"
    properties: GCPServiceAccountNodeProperties = GCPServiceAccountNodeProperties()
    sub_resource_relationship: GCPPrincipalToProjectRel = GCPPrincipalToProjectRel()
    # Service accounts are principals; add shared label for cross-module queries
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["GCPPrincipal"])


# =============================================================================
# Organization-level roles (predefined/basic roles and custom org roles)
# =============================================================================


@dataclass(frozen=True)
class GCPOrgRoleNodeProperties(CartographyNodeProperties):
    """Properties for organization-level roles (predefined and custom org roles)."""

    id: PropertyRef = PropertyRef("name", extra_index=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    title: PropertyRef = PropertyRef("title")
    description: PropertyRef = PropertyRef("description")
    deleted: PropertyRef = PropertyRef("deleted")
    etag: PropertyRef = PropertyRef("etag")
    permissions: PropertyRef = PropertyRef("includedPermissions")
    role_type: PropertyRef = PropertyRef("roleType")  # BASIC, PREDEFINED, or CUSTOM
    scope: PropertyRef = PropertyRef("scope")  # GLOBAL or ORGANIZATION
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    organization_id: PropertyRef = PropertyRef("organizationId", set_in_kwargs=True)


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
    """
    Schema for organization-level GCP IAM Roles.

    This includes:
    - Predefined roles (roles/*) - global roles defined by Google
    - Basic roles (roles/owner, roles/editor, roles/viewer)
    - Custom organization roles (organizations/*/roles/*)

    These roles are sub-resources of GCPOrganization.
    """

    label: str = "GCPRole"
    properties: GCPOrgRoleNodeProperties = GCPOrgRoleNodeProperties()
    sub_resource_relationship: GCPOrgRoleToOrganizationRel = (
        GCPOrgRoleToOrganizationRel()
    )


# =============================================================================
# Project-level roles (custom project roles only)
# =============================================================================


@dataclass(frozen=True)
class GCPProjectRoleNodeProperties(CartographyNodeProperties):
    """Properties for project-level custom roles."""

    id: PropertyRef = PropertyRef("name", extra_index=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    title: PropertyRef = PropertyRef("title")
    description: PropertyRef = PropertyRef("description")
    deleted: PropertyRef = PropertyRef("deleted")
    etag: PropertyRef = PropertyRef("etag")
    permissions: PropertyRef = PropertyRef("includedPermissions")
    role_type: PropertyRef = PropertyRef("roleType")  # Always CUSTOM for project roles
    scope: PropertyRef = PropertyRef("scope")  # Always PROJECT
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    project_id: PropertyRef = PropertyRef("projectId", set_in_kwargs=True)


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
    """
    Schema for project-level GCP IAM Roles.

    This includes only custom project roles (projects/*/roles/*).
    These roles are sub-resources of GCPProject.
    """

    label: str = "GCPRole"
    properties: GCPProjectRoleNodeProperties = GCPProjectRoleNodeProperties()
    sub_resource_relationship: GCPProjectRoleToProjectRel = GCPProjectRoleToProjectRel()
