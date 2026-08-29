from dataclasses import dataclass

from cartography.models.aws.extra_labels import LEGACY_DYNAMO_DB_GLOBAL_SECONDARY_INDEX
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
class DynamoDBGSINodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "Arn", description="The ARN of the global secondary index"
    )
    arn: PropertyRef = PropertyRef(
        "Arn",
        description="The Amazon Resource Name (ARN) of the global secondary index",
    )
    name: PropertyRef = PropertyRef(
        "GSIName", description="The name of the global secondary index"
    )
    region: PropertyRef = PropertyRef(
        "Region", set_in_kwargs=True, description="The AWS region"
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    provisioned_throughput_read_capacity_units: PropertyRef = PropertyRef(
        "ProvisionedThroughputReadCapacityUnits",
        description="The maximum number of read capacity units for the global secondary index",
    )
    provisioned_throughput_write_capacity_units: PropertyRef = PropertyRef(
        "ProvisionedThroughputWriteCapacityUnits",
        description="The maximum number of write capacity units for the global secondary index",
    )


@dataclass(frozen=True)
class DynamoDBGSIToAWSAccountRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AWSDynamoDBGlobalSecondaryIndex)<-[:RESOURCE]-(:AWSAccount)
class DynamoDBGSIToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DynamoDBGSIToAWSAccountRelRelProperties = (
        DynamoDBGSIToAWSAccountRelRelProperties()
    )


@dataclass(frozen=True)
class DynamoDBGSIToDynamoDBTableRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AWSDynamoDBGlobalSecondaryIndex)<-[:GLOBAL_SECONDARY_INDEX]-(:AWSDynamoDBTable)
class DynamoDBGSIToDynamoDBTableRel(CartographyRelSchema):
    target_node_label: str = "AWSDynamoDBTable"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("TableArn")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "GLOBAL_SECONDARY_INDEX"
    properties: DynamoDBGSIToDynamoDBTableRelRelProperties = (
        DynamoDBGSIToDynamoDBTableRelRelProperties()
    )


@dataclass(frozen=True)
class DynamoDBGSISchema(CartographyNodeSchema):
    """Representation of a DynamoDB [Global Secondary Index](https://docs.aws.amazon.com/amazondynamodb/latest/APIReference/API_GlobalSecondaryIndexDescription.html)."""

    label: str = "AWSDynamoDBGlobalSecondaryIndex"
    # DEPRECATED: legacy DynamoDBGlobalSecondaryIndex node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [LEGACY_DYNAMO_DB_GLOBAL_SECONDARY_INDEX]
    )
    properties: DynamoDBGSINodeProperties = DynamoDBGSINodeProperties()
    sub_resource_relationship: DynamoDBGSIToAWSAccountRel = DynamoDBGSIToAWSAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            DynamoDBGSIToDynamoDBTableRel(),
        ],
    )
