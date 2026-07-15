from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class DynamoDBTableNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "Arn", description="Unique identifier for this `AWSDynamoDBTable` node."
    )
    arn: PropertyRef = PropertyRef(
        "Arn",
        extra_index=True,
        description="Amazon Resource Name (ARN) of this `AWSDynamoDBTable` node.",
    )
    name: PropertyRef = PropertyRef(
        "TableName", description="Name of this `AWSDynamoDBTable` node."
    )
    region: PropertyRef = PropertyRef(
        "Region",
        set_in_kwargs=True,
        description="AWS Region containing this `AWSDynamoDBTable` node.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that updated this `AWSDynamoDBTable` node.",
    )

    # Basic table properties
    rows: PropertyRef = PropertyRef(
        "Rows", description="Approximate number of items stored in the table."
    )
    size: PropertyRef = PropertyRef("Size", description="Total table size in bytes.")
    table_status: PropertyRef = PropertyRef(
        "TableStatus",
        description="Current operational status of the table.",
    )
    creation_date_time: PropertyRef = PropertyRef(
        "CreationDateTime",
        description="Timestamp when the table was created.",
    )

    # Provisioned throughput
    provisioned_throughput_read_capacity_units: PropertyRef = PropertyRef(
        "ProvisionedThroughputReadCapacityUnits",
        description="Provisioned read capacity units for the table.",
    )
    provisioned_throughput_write_capacity_units: PropertyRef = PropertyRef(
        "ProvisionedThroughputWriteCapacityUnits",
        description="Provisioned write capacity units for the table.",
    )


@dataclass(frozen=True)
class DynamoDBTableToAWSAccountRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AWSDynamoDBTable)<-[:RESOURCE]-(:AWSAccount)
class DynamoDBTableToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSDynamoDBTable`."

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DynamoDBTableToAWSAccountRelRelProperties = (
        DynamoDBTableToAWSAccountRelRelProperties()
    )


@dataclass(frozen=True)
class DynamoDBTableSchema(CartographyNodeSchema):
    "Represents an `AWSDynamoDBTable` node in the AWS graph."

    label: str = "AWSDynamoDBTable"
    # DEPRECATED: legacy DynamoDBTable node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["DynamoDBTable", "Database"])
    properties: DynamoDBTableNodeProperties = DynamoDBTableNodeProperties()
    sub_resource_relationship: DynamoDBTableToAWSAccountRel = (
        DynamoDBTableToAWSAccountRel()
    )
