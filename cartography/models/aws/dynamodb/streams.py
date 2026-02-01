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
class DynamoDBStreamNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("Arn")
    arn: PropertyRef = PropertyRef("Arn")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    stream_label: PropertyRef = PropertyRef("StreamLabel")
    stream_enabled: PropertyRef = PropertyRef("StreamEnabled")
    stream_view_type: PropertyRef = PropertyRef("StreamViewType")


@dataclass(frozen=True)
class DynamoDBStreamToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DynamoDBStreamToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DynamoDBStreamToAWSAccountRelProperties = (
        DynamoDBStreamToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class DynamoDBStreamToTableRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DynamoDBStreamToTableRel(CartographyRelSchema):
    target_node_label: str = "DynamoDBTable"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TableArn")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "LATEST_STREAM"
    properties: DynamoDBStreamToTableRelProperties = (
        DynamoDBStreamToTableRelProperties()
    )


@dataclass(frozen=True)
class DynamoDBStreamSchema(CartographyNodeSchema):
    label: str = "DynamoDBStream"
    properties: DynamoDBStreamNodeProperties = DynamoDBStreamNodeProperties()
    sub_resource_relationship: DynamoDBStreamToAWSAccountRel = (
        DynamoDBStreamToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            DynamoDBStreamToTableRel(),
        ]
    )
