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
class SQSQueueNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("QueueArn")
    arn: PropertyRef = PropertyRef("QueueArn", extra_index=True)
    name: PropertyRef = PropertyRef("name")
    url: PropertyRef = PropertyRef("url")
    created_timestamp: PropertyRef = PropertyRef("CreatedTimestamp")
    delay_seconds: PropertyRef = PropertyRef("DelaySeconds")
    last_modified_timestamp: PropertyRef = PropertyRef("LastModifiedTimestamp")
    maximum_message_size: PropertyRef = PropertyRef("MaximumMessageSize")
    message_retention_period: PropertyRef = PropertyRef("MessageRetentionPeriod")
    policy: PropertyRef = PropertyRef("Policy")
    receive_message_wait_time_seconds: PropertyRef = PropertyRef(
        "ReceiveMessageWaitTimeSeconds"
    )
    redrive_policy_dead_letter_target_arn: PropertyRef = PropertyRef(
        "redrive_policy_dead_letter_target_arn"
    )
    redrive_policy_max_receive_count: PropertyRef = PropertyRef(
        "redrive_policy_max_receive_count"
    )
    visibility_timeout: PropertyRef = PropertyRef("VisibilityTimeout")
    kms_master_key_id: PropertyRef = PropertyRef("KmsMasterKeyId")
    kms_data_key_reuse_period_seconds: PropertyRef = PropertyRef(
        "KmsDataKeyReusePeriodSeconds"
    )
    fifo_queue: PropertyRef = PropertyRef("FifoQueue")
    content_based_deduplication: PropertyRef = PropertyRef("ContentBasedDeduplication")
    deduplication_scope: PropertyRef = PropertyRef("DeduplicationScope")
    fifo_throughput_limit: PropertyRef = PropertyRef("FifoThroughputLimit")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SQSQueueToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SQSQueueToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SQSQueueToAWSAccountRelProperties = SQSQueueToAWSAccountRelProperties()


@dataclass(frozen=True)
class SQSQueueToDeadLetterQueueRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SQSQueueToDeadLetterQueueRel(CartographyRelSchema):
    target_node_label: str = "SQSQueue"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("redrive_policy_dead_letter_target_arn")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_DEADLETTER_QUEUE"
    properties: SQSQueueToDeadLetterQueueRelProperties = (
        SQSQueueToDeadLetterQueueRelProperties()
    )


@dataclass(frozen=True)
class SQSQueueSchema(CartographyNodeSchema):
    label: str = "SQSQueue"
    properties: SQSQueueNodeProperties = SQSQueueNodeProperties()
    sub_resource_relationship: SQSQueueToAWSAccountRel = SQSQueueToAWSAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [SQSQueueToDeadLetterQueueRel()]
    )
