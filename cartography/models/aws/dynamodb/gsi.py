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
class DynamoDBGSINodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("Arn")
    arn: PropertyRef = PropertyRef("Arn")
    name: PropertyRef = PropertyRef("GSIName")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    provisioned_throughput_read_capacity_units: PropertyRef = PropertyRef(
        "ProvisionedThroughputReadCapacityUnits",
    )
    provisioned_throughput_write_capacity_units: PropertyRef = PropertyRef(
        "ProvisionedThroughputWriteCapacityUnits",
    )


@dataclass(frozen=True)
class DynamoDBGSIToAWSAccountRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DynamoDBGlobalSecondaryIndex)<-[:RESOURCE]-(:AWSAccount)
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
# (:DynamoDBGlobalSecondaryIndex)<-[:GLOBAL_SECONDARY_INDEX]-(:DynamoDBTable)
class DynamoDBGSIToDynamoDBTableRel(CartographyRelSchema):
    target_node_label: str = "DynamoDBTable"
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
    label: str = "DynamoDBGlobalSecondaryIndex"
    properties: DynamoDBGSINodeProperties = DynamoDBGSINodeProperties()
    sub_resource_relationship: DynamoDBGSIToAWSAccountRel = DynamoDBGSIToAWSAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            DynamoDBGSIToDynamoDBTableRel(),
        ],
    )
