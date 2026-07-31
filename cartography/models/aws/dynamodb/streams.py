from dataclasses import dataclass

from cartography.models.aws.extra_labels import LEGACY_DYNAMO_DB_STREAM
from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class DynamoDBStreamNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("Arn", description="The ARN of the stream")
    arn: PropertyRef = PropertyRef("Arn", description="The ARN of the stream")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    stream_label: PropertyRef = PropertyRef(
        "StreamLabel", description="A timestamp used as the stream label"
    )
    stream_enabled: PropertyRef = PropertyRef(
        "StreamEnabled", description="Whether the stream is enabled"
    )
    stream_view_type: PropertyRef = PropertyRef(
        "StreamViewType",
        description="What information is written to the stream (KEYS_ONLY, NEW_IMAGE, OLD_IMAGE, NEW_AND_OLD_IMAGES)",
    )


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
    target_node_label: str = "AWSDynamoDBTable"
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
    """Representation of a DynamoDB [Stream](https://docs.aws.amazon.com/amazondynamodb/latest/APIReference/API_StreamSpecification.html)."""

    label: str = "AWSDynamoDBStream"
    # DEPRECATED: legacy DynamoDBStream node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([LEGACY_DYNAMO_DB_STREAM])
    properties: DynamoDBStreamNodeProperties = DynamoDBStreamNodeProperties()
    sub_resource_relationship: DynamoDBStreamToAWSAccountRel = (
        DynamoDBStreamToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            DynamoDBStreamToTableRel(),
        ]
    )
