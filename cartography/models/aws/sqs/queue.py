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
class SQSQueueNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("QueueArn", description="The arn of the sqs queue.")
    arn: PropertyRef = PropertyRef(
        "QueueArn", extra_index=True, description="The arn of the sqs queue."
    )
    name: PropertyRef = PropertyRef(
        "name", description="Name of this `AWSSQSQueue` node."
    )
    url: PropertyRef = PropertyRef(
        "url", description="Service URL used to address the SQS queue."
    )
    created_timestamp: PropertyRef = PropertyRef(
        "CreatedTimestamp", description="The time when the queue was created in seconds"
    )
    delay_seconds: PropertyRef = PropertyRef(
        "DelaySeconds", description="The default delay on the queue in seconds."
    )
    last_modified_timestamp: PropertyRef = PropertyRef(
        "LastModifiedTimestamp",
        description="The time when the queue was last changed in seconds.",
    )
    maximum_message_size: PropertyRef = PropertyRef(
        "MaximumMessageSize",
        description="The limit of how many bytes a message can contain before Amazon SQS rejects it.",
    )
    message_retention_period: PropertyRef = PropertyRef(
        "MessageRetentionPeriod",
        description="he length of time, in seconds, for which Amazon SQS retains a message.",
    )
    policy: PropertyRef = PropertyRef(
        "Policy", description="The IAM policy of the queue."
    )
    receive_message_wait_time_seconds: PropertyRef = PropertyRef(
        "ReceiveMessageWaitTimeSeconds",
        description="The length of time, in seconds, for which the ReceiveMessage action waits for a message to arrive.",
    )
    redrive_policy_dead_letter_target_arn: PropertyRef = PropertyRef(
        "redrive_policy_dead_letter_target_arn",
        description="The Amazon Resource Name (ARN) of the dead-letter queue to which Amazon SQS moves messages after the value of maxReceiveCount is exceeded.",
    )
    redrive_policy_max_receive_count: PropertyRef = PropertyRef(
        "redrive_policy_max_receive_count",
        description="The number of times a message is delivered to the source queue before being moved to the dead-letter queue. When the ReceiveCount for a message exceeds the maxReceiveCount for a queue, Amazon SQS moves the message to the dead-letter-queue.",
    )
    visibility_timeout: PropertyRef = PropertyRef(
        "VisibilityTimeout", description="The visibility timeout for the queue."
    )
    kms_master_key_id: PropertyRef = PropertyRef(
        "KmsMasterKeyId",
        description="The ID of an AWS managed customer master key (CMK) for Amazon SQS or a custom CMK.",
    )
    kms_data_key_reuse_period_seconds: PropertyRef = PropertyRef(
        "KmsDataKeyReusePeriodSeconds",
        description="The length of time, in seconds, for which Amazon SQS can reuse a data key to encrypt or decrypt messages before calling AWS KMS again.",
    )
    fifo_queue: PropertyRef = PropertyRef(
        "FifoQueue", description="Whether or not the queue is FIFO."
    )
    content_based_deduplication: PropertyRef = PropertyRef(
        "ContentBasedDeduplication",
        description="Whether or not content-based deduplication is enabled for the queue.",
    )
    deduplication_scope: PropertyRef = PropertyRef(
        "DeduplicationScope",
        description="Specifies whether message deduplication occurs at the message group or queue level.",
    )
    fifo_throughput_limit: PropertyRef = PropertyRef(
        "FifoThroughputLimit",
        description="Specifies whether the FIFO queue throughput quota applies to the entire queue or per message group.",
    )
    region: PropertyRef = PropertyRef(
        "Region",
        set_in_kwargs=True,
        description="AWS Region containing this `AWSSQSQueue` node.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )


@dataclass(frozen=True)
class SQSQueueToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SQSQueueToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSSQSQueue`."

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
    "Represents a `HAS_DEADLETTER_QUEUE` relationship from `AWSSQSQueue` to `AWSSQSQueue`."

    target_node_label: str = "AWSSQSQueue"
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
    "Represents an `AWSSQSQueue` node in the AWS graph."

    label: str = "AWSSQSQueue"
    # DEPRECATED: legacy SQSQueue node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["SQSQueue"])
    properties: SQSQueueNodeProperties = SQSQueueNodeProperties()
    sub_resource_relationship: SQSQueueToAWSAccountRel = SQSQueueToAWSAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [SQSQueueToDeadLetterQueueRel()]
    )
