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
class SNSTopicNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("TopicArn")
    arn: PropertyRef = PropertyRef("TopicArn", extra_index=True)
    name: PropertyRef = PropertyRef("TopicName")
    displayname: PropertyRef = PropertyRef("DisplayName")
    owner: PropertyRef = PropertyRef("Owner")
    subscriptionspending: PropertyRef = PropertyRef("SubscriptionsPending")
    subscriptionsconfirmed: PropertyRef = PropertyRef("SubscriptionsConfirmed")
    subscriptionsdeleted: PropertyRef = PropertyRef("SubscriptionsDeleted")
    deliverypolicy: PropertyRef = PropertyRef("DeliveryPolicy")
    effectivedeliverypolicy: PropertyRef = PropertyRef("EffectiveDeliveryPolicy")
    kmsmasterkeyid: PropertyRef = PropertyRef("KmsMasterKeyId")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SNSTopicToAwsAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SNSTopicToAWSAccount(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SNSTopicToAwsAccountRelProperties = SNSTopicToAwsAccountRelProperties()


@dataclass(frozen=True)
class SNSTopicSchema(CartographyNodeSchema):
    label: str = "SNSTopic"
    properties: SNSTopicNodeProperties = SNSTopicNodeProperties()
    sub_resource_relationship: SNSTopicToAWSAccount = SNSTopicToAWSAccount()
