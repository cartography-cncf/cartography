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
class GCPCloudRunExecutionProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    job: PropertyRef = PropertyRef("job")
    cancelled_count: PropertyRef = PropertyRef("cancelled_count")
    failed_count: PropertyRef = PropertyRef("failed_count")
    succeeded_count: PropertyRef = PropertyRef("succeeded_count")
    project_id: PropertyRef = PropertyRef("project_id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProjectToCloudRunExecutionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProjectToCloudRunExecutionRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("project_id", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ProjectToCloudRunExecutionRelProperties = (
        ProjectToCloudRunExecutionRelProperties()
    )


@dataclass(frozen=True)
class CloudRunJobToExecutionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class CloudRunJobToExecutionRel(CartographyRelSchema):
    target_node_label: str = "GCPCloudRunJob"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("job")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_EXECUTION"
    properties: CloudRunJobToExecutionRelProperties = (
        CloudRunJobToExecutionRelProperties()
    )


@dataclass(frozen=True)
class GCPCloudRunExecutionSchema(CartographyNodeSchema):
    label: str = "GCPCloudRunExecution"
    properties: GCPCloudRunExecutionProperties = GCPCloudRunExecutionProperties()
    sub_resource_relationship: ProjectToCloudRunExecutionRel = (
        ProjectToCloudRunExecutionRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            CloudRunJobToExecutionRel(),
        ],
    )
