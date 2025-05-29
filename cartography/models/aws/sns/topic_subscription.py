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
class SNSTopicSubscriptionNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("SubscriptionArn")
    arn: PropertyRef = PropertyRef("SubscriptionArn", extra_index=True)
    subscription_arn: PropertyRef = PropertyRef("SubscriptionArn")
    topic_arn: PropertyRef = PropertyRef("TopicArn")
    confirmation_was_authenticated: PropertyRef = PropertyRef(
        "ConfirmationWasAuthenticated"
    )
    delivery_policy: PropertyRef = PropertyRef("DeliveryPolicy")
    effective_delivery_policy: PropertyRef = PropertyRef("EffectiveDeliveryPolicy")
    filter_policy: PropertyRef = PropertyRef("FilterPolicy")
    filter_policy_scope: PropertyRef = PropertyRef("FilterPolicyScope")
    owner: PropertyRef = PropertyRef("Owner")
    pending_confirmation: PropertyRef = PropertyRef("PendingConfirmation")
    raw_message_delivery: PropertyRef = PropertyRef("RawMessageDelivery")
    redrive_policy: PropertyRef = PropertyRef("RedrivePolicy")
    subscription_role_arn: PropertyRef = PropertyRef("SubscriptionRoleArn")
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
class SNSTopicSubscriptionSchema(CartographyNodeSchema):
    label: str = "SNSTopicSubscription"
    properties: SNSTopicSubscriptionNodeProperties = (
        SNSTopicSubscriptionNodeProperties()
    )
    sub_resource_relationship: SNSTopicSubscriptionToAWSAccountRel = (
        SNSTopicSubscriptionToAWSAccountRel()
    )
