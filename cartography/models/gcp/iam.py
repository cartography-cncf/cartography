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
from cartography.models.core.relationships import OtherRelationships
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
class GCPRoleNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("name", extra_index=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    title: PropertyRef = PropertyRef("title")
    description: PropertyRef = PropertyRef("description")
    deleted: PropertyRef = PropertyRef("deleted")
    etag: PropertyRef = PropertyRef("etag")
    permissions: PropertyRef = PropertyRef("includedPermissions")
    role_type: PropertyRef = PropertyRef("roleType")
    scope: PropertyRef = PropertyRef("scope")  # GLOBAL, PROJECT, or ORGANIZATION
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    project_id: PropertyRef = PropertyRef("projectId")  # Set from data, not kwargs
    organization_id: PropertyRef = PropertyRef("organizationId", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPIAMToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:GCPUser|GCPServiceAccount|GCPRole)<-[:RESOURCE]-(:GCPProject)
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


@dataclass(frozen=True)
class GCPRoleToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPRoleToOrganizationRel(CartographyRelSchema):
    """Relationship connecting GCPRole to GCPOrganization."""

    target_node_label: str = "GCPOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("organizationId", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPRoleToOrganizationRelProperties = (
        GCPRoleToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class GCPRoleToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPRoleToProjectRel(CartographyRelSchema):
    """Relationship connecting project-level GCPRole to GCPProject."""

    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("projectId")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPRoleToProjectRelProperties = GCPRoleToProjectRelProperties()


@dataclass(frozen=True)
class GCPRoleSchema(CartographyNodeSchema):
    """
    Schema for GCP IAM Roles.

    Roles are connected to GCPOrganization as their primary sub-resource.
    Project-level custom roles are additionally connected to their GCPProject.
    """

    label: str = "GCPRole"
    properties: GCPRoleNodeProperties = GCPRoleNodeProperties()
    sub_resource_relationship: GCPRoleToOrganizationRel = GCPRoleToOrganizationRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [GCPRoleToProjectRel()],
    )
