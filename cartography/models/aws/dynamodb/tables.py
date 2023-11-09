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
class DynamoDBTableNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef('Arn')
    arn: PropertyRef = PropertyRef('Arn')
    name: PropertyRef = PropertyRef('TableName')
    region: PropertyRef = PropertyRef('Region', set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)
    rows: PropertyRef = PropertyRef('Rows')
    size: PropertyRef = PropertyRef('Size')
    provisioned_throughput_read_capacity_units: PropertyRef = PropertyRef('ProvisionedThroughputReadCapacityUnits')
    provisioned_throughput_write_capacity_units: PropertyRef = PropertyRef('ProvisionedThroughputWriteCapacityUnits')


@dataclass(frozen=True)
class DynamoDBTableToAwsAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
# (:DynamoDBTable)<-[:RESOURCE]-(:AWSAccount)
class DynamoDBTableToAWSAccount(CartographyRelSchema):
    target_node_label: str = 'AWSAccount'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('AWS_ID', set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DynamoDBTableToAwsAccountRelProperties = DynamoDBTableToAwsAccountRelProperties()


@dataclass(frozen=True)
class DynamoDBTableSchema(CartographyNodeSchema):
    label: str = 'DynamoDBTable'
    properties: DynamoDBTableNodeProperties = DynamoDBTableNodeProperties()
    sub_resource_relationship: DynamoDBTableToAWSAccount = DynamoDBTableToAWSAccount()
