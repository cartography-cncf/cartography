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
class DataPipelineNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("Id")
    arn: PropertyRef = PropertyRef("Arn", extra_index=True)
    pipeline_id: PropertyRef = PropertyRef("PipelineId")
    name: PropertyRef = PropertyRef("Name")
    description: PropertyRef = PropertyRef("Description")
    unique_id: PropertyRef = PropertyRef("UniqueId")
    state: PropertyRef = PropertyRef("State")
    health_status: PropertyRef = PropertyRef("HealthStatus")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DataPipelineToAwsAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DataPipelineToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DataPipelineToAwsAccountRelProperties = (
        DataPipelineToAwsAccountRelProperties()
    )


@dataclass(frozen=True)
class DataPipelineSchema(CartographyNodeSchema):
    label: str = "DataPipeline"
    properties: DataPipelineNodeProperties = DataPipelineNodeProperties()
    sub_resource_relationship: DataPipelineToAWSAccountRel = (
        DataPipelineToAWSAccountRel()
    )
