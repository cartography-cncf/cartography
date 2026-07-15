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
class DynamoDBBillingModeSummaryNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "Id", description='Unique identifier (table ARN + "/billing")'
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )
    billing_mode: PropertyRef = PropertyRef(
        "BillingMode", description="The billing mode (PROVISIONED or PAY_PER_REQUEST)"
    )
    last_update_to_pay_per_request_date_time: PropertyRef = PropertyRef(
        "LastUpdateToPayPerRequestDateTime",
        description="When the table was last switched to PAY_PER_REQUEST mode",
    )


@dataclass(frozen=True)
class DynamoDBBillingModeSummaryToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DynamoDBBillingModeSummaryToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSDynamoDBBillingModeSummary`."

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DynamoDBBillingModeSummaryToAWSAccountRelProperties = (
        DynamoDBBillingModeSummaryToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class DynamoDBBillingModeSummaryToTableRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DynamoDBBillingModeSummaryToTableRel(CartographyRelSchema):
    "Represents a `HAS_BILLING` relationship from `AWSDynamoDBTable` to `AWSDynamoDBBillingModeSummary`."

    target_node_label: str = "AWSDynamoDBTable"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TableArn")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_BILLING"
    properties: DynamoDBBillingModeSummaryToTableRelProperties = (
        DynamoDBBillingModeSummaryToTableRelProperties()
    )


@dataclass(frozen=True)
class DynamoDBBillingModeSummarySchema(CartographyNodeSchema):
    "Represents an `AWSDynamoDBBillingModeSummary` node in the AWS graph."

    label: str = "AWSDynamoDBBillingModeSummary"
    # DEPRECATED: legacy DynamoDBBillingModeSummary node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["DynamoDBBillingModeSummary"])
    properties: DynamoDBBillingModeSummaryNodeProperties = (
        DynamoDBBillingModeSummaryNodeProperties()
    )
    sub_resource_relationship: DynamoDBBillingModeSummaryToAWSAccountRel = (
        DynamoDBBillingModeSummaryToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            DynamoDBBillingModeSummaryToTableRel(),
        ]
    )
