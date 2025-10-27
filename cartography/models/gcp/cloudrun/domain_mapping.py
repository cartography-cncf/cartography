import logging
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

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class GCPCloudRunDomainMappingProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")  # The domain name
    route_name: PropertyRef = PropertyRef("route_name")  # The service it points to
    project_id: PropertyRef = PropertyRef("project_id", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProjectToDomainMappingRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProjectToDomainMappingRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("project_id", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ProjectToDomainMappingRelProperties = (
        ProjectToDomainMappingRelProperties()
    )


@dataclass(frozen=True)
class DomainMappingToServiceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DomainMappingToServiceRel(CartographyRelSchema):
    target_node_label: str = "GCPCloudRunService"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"name": PropertyRef("route_name")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "POINTS_TO_SERVICE"
    properties: DomainMappingToServiceRelProperties = (
        DomainMappingToServiceRelProperties()
    )


@dataclass(frozen=True)
class GCPCloudRunDomainMappingSchema(CartographyNodeSchema):
    label: str = "GCPCloudRunDomainMapping"
    properties: GCPCloudRunDomainMappingProperties = (
        GCPCloudRunDomainMappingProperties()
    )
    sub_resource_relationship: ProjectToDomainMappingRel = ProjectToDomainMappingRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            DomainMappingToServiceRel(),
        ],
    )
