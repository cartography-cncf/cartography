from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class GCPCloudFunctionProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("name", extra_index=True)
    name: PropertyRef = PropertyRef("name")
    description: PropertyRef = PropertyRef("description")
    runtime: PropertyRef = PropertyRef("runtime")
    entry_point: PropertyRef = PropertyRef("entryPoint")
    status: PropertyRef = PropertyRef("status")
    update_time: PropertyRef = PropertyRef("updateTime")
    service_account_email: PropertyRef = PropertyRef("serviceAccountEmail")
    https_trigger_url: PropertyRef = PropertyRef("https_trigger_url")
    event_trigger_type: PropertyRef = PropertyRef("event_trigger_type")
    event_trigger_resource: PropertyRef = PropertyRef("event_trigger_resource")
    project_id: PropertyRef = PropertyRef("projectId", set_in_kwargs=True)
    region: PropertyRef = PropertyRef("region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPCloudFunctionToGCPProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPCloudFunctionToGCPProjectRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("projectId", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPCloudFunctionToGCPProjectRelProperties = (
        GCPCloudFunctionToGCPProjectRelProperties()
    )


@dataclass(frozen=True)
class GCPCloudFunctionToGCPServiceAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


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
    sub_resource_relationship: GCPCloudFunctionToGCPProjectRel = (
        GCPCloudFunctionToGCPProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GCPCloudFunctionToGCPServiceAccountRel(),
        ],
    )
