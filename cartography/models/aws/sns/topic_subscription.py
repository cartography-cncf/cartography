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
class SNSTopicSubscriptionNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("SubscriptionArn")
    arn: PropertyRef = PropertyRef("SubscriptionArn", extra_index=True)
    topic_arn: PropertyRef = PropertyRef("TopicArn")
    endpoint: PropertyRef = PropertyRef("Endpoint")
    owner: PropertyRef = PropertyRef("Owner")
    protocol: PropertyRef = PropertyRef("Protocol")
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
    target_node_label: str = "SNSTopic"
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
    label: str = "SNSTopicSubscription"
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
