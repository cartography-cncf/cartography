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
class CloudWatchLogGroupNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("logGroupArn", description="The ARN of the log group")
    arn: PropertyRef = PropertyRef(
        "logGroupArn",
        extra_index=True,
        description="The Amazon Resource Name (ARN) of the log group",
    )
    creation_time: PropertyRef = PropertyRef(
        "creationTime",
        description="The creation time of the log group, expressed as the number of milliseconds after Jan 1, 1970 00:00:00 UTC",
    )
    data_protection_status: PropertyRef = PropertyRef(
        "dataProtectionStatus",
        description="Displays whether this log group has a protection policy, or whether it had one in the past",
    )
    inherited_properties: PropertyRef = PropertyRef(
        "inheritedProperties",
        description="Displays all the properties that this log group has inherited from account-level settings",
    )
    kms_key_id: PropertyRef = PropertyRef(
        "kmsKeyId",
        description="The Amazon Resource Name (ARN) of the AWS KMS key to use when encrypting log data",
    )
    log_group_arn: PropertyRef = PropertyRef(
        "logGroupArn", description="The Amazon Resource Name (ARN) of the log group"
    )
    log_group_class: PropertyRef = PropertyRef(
        "logGroupClass",
        description="This specifies the log group class for this log group",
    )
    log_group_name: PropertyRef = PropertyRef(
        "logGroupName", description="The name of the log group"
    )
    metric_filter_count: PropertyRef = PropertyRef(
        "metricFilterCount", description="The number of metric filters"
    )
    retention_in_days: PropertyRef = PropertyRef(
        "retentionInDays",
        description="The number of days to retain the log events in the specified log group",
    )
    stored_bytes: PropertyRef = PropertyRef(
        "storedBytes", description="The number of bytes stored"
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )


@dataclass(frozen=True)
class CloudWatchLogGroupToAwsAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class CloudWatchToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSCloudWatchLogGroup`."

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: CloudWatchLogGroupToAwsAccountRelProperties = (
        CloudWatchLogGroupToAwsAccountRelProperties()
    )


@dataclass(frozen=True)
class CloudWatchLogGroupSchema(CartographyNodeSchema):
    "Represents an `AWSCloudWatchLogGroup` node in the AWS graph."

    label: str = "AWSCloudWatchLogGroup"
    # DEPRECATED: legacy CloudWatchLogGroup node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["CloudWatchLogGroup"])
    properties: CloudWatchLogGroupNodeProperties = CloudWatchLogGroupNodeProperties()
    sub_resource_relationship: CloudWatchToAWSAccountRel = CloudWatchToAWSAccountRel()
