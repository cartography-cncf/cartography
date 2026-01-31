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
    arn: PropertyRef = PropertyRef("id", extra_index=True)
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    description: PropertyRef = PropertyRef("description")
    state: PropertyRef = PropertyRef("state")
    user_id: PropertyRef = PropertyRef("userId")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)


@dataclass(frozen=True)
class DataPipelineToAWSAccountRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DataPipeline)<-[:RESOURCE]-(:AWSAccount)
class DataPipelineToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DataPipelineToAWSAccountRelRelProperties = (
        DataPipelineToAWSAccountRelRelProperties()
    )


@dataclass(frozen=True)
class DataPipelineSchema(CartographyNodeSchema):
    label: str = "DataPipeline"
    properties: DataPipelineNodeProperties = DataPipelineNodeProperties()
    sub_resource_relationship: DataPipelineToAWSAccountRel = DataPipelineToAWSAccountRel()
