import logging
from dataclasses import dataclass
from typing import Optional

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class GCPServiceAccountNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef('id', extra_index=True)
    email: PropertyRef = PropertyRef('email', extra_index=True)
    display_name: PropertyRef = PropertyRef('displayName')
    oauth2_client_id: PropertyRef = PropertyRef('oauth2ClientId')
    unique_id: PropertyRef = PropertyRef('uniqueId')
    disabled: PropertyRef = PropertyRef('disabled')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)
    project_id: PropertyRef = PropertyRef('projectId', set_in_kwargs=True)


@dataclass(frozen=True)
class GCPRoleNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef('id', extra_index=True)
    name: PropertyRef = PropertyRef('name', extra_index=True)
    title: PropertyRef = PropertyRef('title')
    description: PropertyRef = PropertyRef('description')
    deleted: PropertyRef = PropertyRef('deleted')
    etag: PropertyRef = PropertyRef('etag')
    permissions: PropertyRef = PropertyRef('includedPermissions')
    role_type: PropertyRef = PropertyRef('roleType')
    scope: PropertyRef = PropertyRef('scope')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)
    organization_id: PropertyRef = PropertyRef('organizationId', set_in_kwargs=True)


@dataclass(frozen=True)
class GCPServiceAccountToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
# (:GCPServiceAccount)<-[:RESOURCE]-(:GCPProject)
class GCPServiceAccountToProject(CartographyRelSchema):
    target_node_label: str = 'GCPProject'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('projectId', set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPServiceAccountToProjectRelProperties = GCPServiceAccountToProjectRelProperties()


@dataclass(frozen=True)
class GCPServiceAccountSchema(CartographyNodeSchema):
    label: str = 'GCPServiceAccount'
    properties: GCPServiceAccountNodeProperties = GCPServiceAccountNodeProperties()
    sub_resource_relationship: GCPServiceAccountToProject = GCPServiceAccountToProject()


@dataclass(frozen=True)
class GCPRoleToOrgRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class GCPRoleToOrg(CartographyRelSchema):
    target_node_label: str = 'GCPOrganization'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('organizationId', set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPRoleToOrgRelProperties = GCPRoleToOrgRelProperties()


@dataclass(frozen=True)
class GCPRoleToProject(CartographyRelSchema):
    target_node_label: str = 'GCPProject'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('projectId', set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPRoleToOrgRelProperties = GCPRoleToOrgRelProperties()


@dataclass(frozen=True)
class GCPRoleSchema(CartographyNodeSchema):
    """
    Schema for GCP IAM Roles.
    - GLOBAL: Role is attached to all GCPProjects and the GCPOrganization
    - PROJECT: Custom role attached to both specific project and organization
    - ORGANIZATION: Custom role attached only to the specific organization
    """
    label: str = 'GCPRole'
    properties: GCPRoleNodeProperties = GCPRoleNodeProperties()
    sub_resource_relationship: CartographyRelSchema = GCPRoleToOrg()

    @property
    def other_relationships(self) -> Optional[OtherRelationships]:
        return OtherRelationships([GCPRoleToProject()])
