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
class DynamoDBBillingModeSummaryNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("Id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    billing_mode: PropertyRef = PropertyRef("BillingMode")
    last_update_to_pay_per_request_date_time: PropertyRef = PropertyRef(
        "LastUpdateToPayPerRequestDateTime",
    )


@dataclass(frozen=True)
class DynamoDBBillingModeSummaryToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DynamoDBBillingModeSummaryToAWSAccountRel(CartographyRelSchema):
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
    target_node_label: str = "DynamoDBTable"
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
    label: str = "DynamoDBBillingModeSummary"
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
