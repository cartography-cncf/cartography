import logging
from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
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
    id: PropertyRef = PropertyRef('name', extra_index=True)
    name: PropertyRef = PropertyRef('name', extra_index=True)
    title: PropertyRef = PropertyRef('title')
    description: PropertyRef = PropertyRef('description')
    deleted: PropertyRef = PropertyRef('deleted')
    etag: PropertyRef = PropertyRef('etag')
    permissions: PropertyRef = PropertyRef('includedPermissions')
    role_type: PropertyRef = PropertyRef('roleType')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)
    project_id: PropertyRef = PropertyRef('projectId', set_in_kwargs=True)


@dataclass(frozen=True)
class GCPIAMToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
# (:GCPUser|GCPServiceAccount|GCPRole)<-[:RESOURCE]-(:GCPProject)
class GCPPrincipalToProject(CartographyRelSchema):
    target_node_label: str = 'GCPProject'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('projectId', set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPIAMToProjectRelProperties = GCPIAMToProjectRelProperties()


@dataclass(frozen=True)
class GCPServiceAccountSchema(CartographyNodeSchema):
    label: str = 'GCPServiceAccount'
    properties: GCPServiceAccountNodeProperties = GCPServiceAccountNodeProperties()
    sub_resource_relationship: GCPPrincipalToProject = GCPPrincipalToProject()


@dataclass(frozen=True)
class GCPRoleSchema(CartographyNodeSchema):
    label: str = 'GCPRole'
    properties: GCPRoleNodeProperties = GCPRoleNodeProperties()
    sub_resource_relationship: GCPPrincipalToProject = GCPPrincipalToProject()
