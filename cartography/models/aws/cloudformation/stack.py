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
class AWSCloudFormationStackNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("StackId")
    name: PropertyRef = PropertyRef("StackName")
    arn: PropertyRef = PropertyRef("StackId")
    creation_time: PropertyRef = PropertyRef("CreationTime")
    last_updated_time: PropertyRef = PropertyRef("LastUpdatedTime")
    stack_status: PropertyRef = PropertyRef("StackStatus")
    description: PropertyRef = PropertyRef("Description")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSCloudFormationStackToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSCloudFormationStackToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AWSCloudFormationStackToAWSAccountRelProperties = (
        AWSCloudFormationStackToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class AWSCloudFormationStackSchema(CartographyNodeSchema):
    label: str = "AWSCloudFormationStack"
    properties: AWSCloudFormationStackNodeProperties = (
        AWSCloudFormationStackNodeProperties()
    )
    sub_resource_relationship: AWSCloudFormationStackToAWSAccountRel = (
        AWSCloudFormationStackToAWSAccountRel()
    )
