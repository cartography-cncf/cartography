from dataclasses import dataclass

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
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )
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
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSDynamoDBGlobalSecondaryIndex`."

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
    "Represents a `GLOBAL_SECONDARY_INDEX` relationship from `AWSDynamoDBTable` to `AWSDynamoDBGlobalSecondaryIndex`."

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
    "Represents an `AWSDynamoDBGlobalSecondaryIndex` node in the AWS graph."

    label: str = "AWSDynamoDBGlobalSecondaryIndex"
    # DEPRECATED: legacy DynamoDBGlobalSecondaryIndex node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        ["DynamoDBGlobalSecondaryIndex"]
    )
    properties: DynamoDBGSINodeProperties = DynamoDBGSINodeProperties()
    sub_resource_relationship: DynamoDBGSIToAWSAccountRel = DynamoDBGSIToAWSAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            DynamoDBGSIToDynamoDBTableRel(),
        ],
    )
