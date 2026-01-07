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
class GCPCloudRunDomainMappingProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    route_name: PropertyRef = PropertyRef("route_name")
    project_id: PropertyRef = PropertyRef("project_id")
    firstseen: PropertyRef = PropertyRef("firstseen", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProjectToCloudRunDomainMappingRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProjectToCloudRunDomainMappingRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("project_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ProjectToCloudRunDomainMappingRelProperties = (
        ProjectToCloudRunDomainMappingRelProperties()
    )


@dataclass(frozen=True)
class CloudRunDomainMappingToServiceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class CloudRunDomainMappingToServiceRel(CartographyRelSchema):
    target_node_label: str = "GCPCloudRunService"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("route_name")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "POINTS_TO_SERVICE"
    properties: CloudRunDomainMappingToServiceRelProperties = (
        CloudRunDomainMappingToServiceRelProperties()
    )


@dataclass(frozen=True)
class GCPCloudRunDomainMappingSchema(CartographyNodeSchema):
    label: str = "GCPCloudRunDomainMapping"
    properties: GCPCloudRunDomainMappingProperties = (
        GCPCloudRunDomainMappingProperties()
    )
    sub_resource_relationship: ProjectToCloudRunDomainMappingRel = (
        ProjectToCloudRunDomainMappingRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            CloudRunDomainMappingToServiceRel(),
        ],
    )
