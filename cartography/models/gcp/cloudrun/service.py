from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class GCPCloudRunServiceProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    description: PropertyRef = PropertyRef("description")
    location: PropertyRef = PropertyRef("location")
    uri: PropertyRef = PropertyRef("uri")
    latest_ready_revision: PropertyRef = PropertyRef("latest_ready_revision")
    project_id: PropertyRef = PropertyRef("project_id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProjectToCloudRunServiceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProjectToCloudRunServiceRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("project_id", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ProjectToCloudRunServiceRelProperties = (
        ProjectToCloudRunServiceRelProperties()
    )


@dataclass(frozen=True)
class GCPCloudRunServiceSchema(CartographyNodeSchema):
    label: str = "GCPCloudRunService"
    properties: GCPCloudRunServiceProperties = GCPCloudRunServiceProperties()
    sub_resource_relationship: ProjectToCloudRunServiceRel = (
        ProjectToCloudRunServiceRel()
    )
