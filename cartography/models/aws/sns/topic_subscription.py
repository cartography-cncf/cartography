from dataclasses import dataclass

from cartography.models.aws.extra_labels import LEGACY_SNS_TOPIC_SUBSCRIPTION
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
class SNSTopicSubscriptionNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "SubscriptionArn", description="The ARN of the SNS topic subscription"
    )
    arn: PropertyRef = PropertyRef(
        "SubscriptionArn",
        extra_index=True,
        description="The Amazon Resource Name (ARN) of the topic subscription",
    )
    topic_arn: PropertyRef = PropertyRef(
        "TopicArn", description="The topic ARN that the subscription is associated with"
    )
    endpoint: PropertyRef = PropertyRef(
        "Endpoint", description="The subscription's endpoint"
    )
    owner: PropertyRef = PropertyRef("Owner", description="The subscription's owner")
    protocol: PropertyRef = PropertyRef(
        "Protocol", description="The subscription's protocol for messages"
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SNSTopicSubscriptionToAwsAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SNSTopicSubscriptionToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SNSTopicSubscriptionToAwsAccountRelProperties = (
        SNSTopicSubscriptionToAwsAccountRelProperties()
    )


@dataclass(frozen=True)
class SNSTopicSubscriptionToSNSTopicRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SNSTopicSubscriptionToSNSTopicRel(CartographyRelSchema):
    target_node_label: str = "AWSSNSTopic"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TopicArn")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_SUBSCRIPTION"
    properties: SNSTopicSubscriptionToSNSTopicRelProperties = (
        SNSTopicSubscriptionToSNSTopicRelProperties()
    )


@dataclass(frozen=True)
class SNSTopicSubscriptionSchema(CartographyNodeSchema):
    """Representation of an AWS [SNS Topic Subscription](https://docs.aws.amazon.com/sns/latest/api/API_GetSubscriptionAttributes.html)"""

    label: str = "AWSSNSTopicSubscription"
    # DEPRECATED: legacy SNSTopicSubscription node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [LEGACY_SNS_TOPIC_SUBSCRIPTION]
    )
    properties: SNSTopicSubscriptionNodeProperties = (
        SNSTopicSubscriptionNodeProperties()
    )
    sub_resource_relationship: SNSTopicSubscriptionToAWSAccountRel = (
        SNSTopicSubscriptionToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            SNSTopicSubscriptionToSNSTopicRel(),
        ]
    )
