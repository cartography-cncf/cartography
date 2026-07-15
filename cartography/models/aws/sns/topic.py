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
class SNSTopicNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("TopicArn", description="The ARN of the SNS topic")
    arn: PropertyRef = PropertyRef(
        "TopicArn",
        extra_index=True,
        description="The Amazon Resource Name (ARN) of the topic",
    )
    name: PropertyRef = PropertyRef("TopicName", description="The name of the topic")
    displayname: PropertyRef = PropertyRef(
        "DisplayName", description="The display name of the topic"
    )
    owner: PropertyRef = PropertyRef(
        "Owner", description="The AWS account ID of the topic's owner"
    )
    subscriptionspending: PropertyRef = PropertyRef(
        "SubscriptionsPending",
        description="The number of subscriptions pending confirmation",
    )
    subscriptionsconfirmed: PropertyRef = PropertyRef(
        "SubscriptionsConfirmed", description="The number of confirmed subscriptions"
    )
    subscriptionsdeleted: PropertyRef = PropertyRef(
        "SubscriptionsDeleted", description="The number of deleted subscriptions"
    )
    deliverypolicy: PropertyRef = PropertyRef(
        "DeliveryPolicy",
        description="The JSON serialization of the topic's delivery policy",
    )
    effectivedeliverypolicy: PropertyRef = PropertyRef(
        "EffectiveDeliveryPolicy",
        description="The JSON serialization of the effective delivery policy",
    )
    kmsmasterkeyid: PropertyRef = PropertyRef(
        "KmsMasterKeyId",
        description="The ID of an AWS managed customer master key (CMK) for Amazon SNS or a custom CMK",
    )
    region: PropertyRef = PropertyRef(
        "Region",
        set_in_kwargs=True,
        description="The AWS region where the topic is located",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )


@dataclass(frozen=True)
class SNSTopicToAwsAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SNSTopicToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSSNSTopic`."

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SNSTopicToAwsAccountRelProperties = SNSTopicToAwsAccountRelProperties()


@dataclass(frozen=True)
class SNSTopicSchema(CartographyNodeSchema):
    "Represents an `AWSSNSTopic` node in the AWS graph."

    label: str = "AWSSNSTopic"
    # DEPRECATED: legacy SNSTopic node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["SNSTopic"])
    properties: SNSTopicNodeProperties = SNSTopicNodeProperties()
    sub_resource_relationship: SNSTopicToAWSAccountRel = SNSTopicToAWSAccountRel()
