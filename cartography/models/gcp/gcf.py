
import logging
from dataclasses import dataclass
from typing import Optional

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties, CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties, CartographyRelSchema, LinkDirection, make_target_node_matcher, TargetNodeMatcher, OtherRelationships
from cartography.models.gcp.iam import GCPPrincipalToProject

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class GCPCloudFunctionProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef('name', extra_index=True)
    name: PropertyRef = PropertyRef('name')
    display_name: PropertyRef = PropertyRef('displayName')
    description: PropertyRef = PropertyRef('description')
    runtime: PropertyRef = PropertyRef('runtime')
    entry_point: PropertyRef = PropertyRef('entryPoint')
    status: PropertyRef = PropertyRef('state')
    create_time: PropertyRef = PropertyRef('createTime')
    update_time: PropertyRef = PropertyRef('updateTime')
    service_account_email: PropertyRef = PropertyRef('serviceAccountEmail')
    https_trigger_url: PropertyRef = PropertyRef('https_trigger_url')
    event_trigger_type: PropertyRef = PropertyRef('event_trigger_type')
    event_trigger_resource: PropertyRef = PropertyRef('event_trigger_resource')
    project_id: PropertyRef = PropertyRef('projectId', set_in_kwargs=True)
    region: PropertyRef = PropertyRef('region', set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class GCPCloudFunctionToGCPServiceAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class GCPCloudFunctionToGCPServiceAccountRel(CartographyRelSchema):
    target_node_label: str = "GCPServiceAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"email": PropertyRef("serviceAccountEmail")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RUNS_AS"
    properties: GCPCloudFunctionToGCPServiceAccountRelProperties = (
        GCPCloudFunctionToGCPServiceAccountRelProperties()
    )


@dataclass(frozen=True)
class GCPCloudFunctionSchema(CartographyNodeSchema):
    label: str = "GCPCloudFunction"
    properties: GCPCloudFunctionProperties = GCPCloudFunctionProperties()
    # This now reuses the generic relationship from the iam model
    sub_resource_relationship: GCPPrincipalToProject = GCPPrincipalToProject()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GCPCloudFunctionToGCPServiceAccountRel(),
        ],
    )