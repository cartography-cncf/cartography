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
class CloudWatchMetricAlarmNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "AlarmArn", description="The ARN of the CloudWatch Metric Alarm"
    )
    arn: PropertyRef = PropertyRef(
        "AlarmArn",
        extra_index=True,
        description="The ARN of the CloudWatch Metric Alarm",
    )
    alarm_name: PropertyRef = PropertyRef(
        "AlarmName", description="The name of the alarm"
    )
    alarm_description: PropertyRef = PropertyRef(
        "AlarmDescription", description="The description of the alarm"
    )
    state_value: PropertyRef = PropertyRef(
        "StateValue", description="The state value for the alarm"
    )
    state_reason: PropertyRef = PropertyRef(
        "StateReason", description="An explanation for the alarm state, in text format"
    )
    actions_enabled: PropertyRef = PropertyRef(
        "ActionsEnabled",
        description="Indicates whether actions should be executed during any changes to the alarm state",
    )
    comparison_operator: PropertyRef = PropertyRef(
        "ComparisonOperator",
        description="The arithmetic operation to use when comparing the specified statistic and threshold. The specified statistic value is used as the first operand",
    )
    region: PropertyRef = PropertyRef(
        "Region",
        set_in_kwargs=True,
        description="The region of the CloudWatch Metric Alarm",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )


@dataclass(frozen=True)
class CloudWatchMetricAlarmToAwsAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class CloudWatchMetricAlarmToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSCloudWatchMetricAlarm`."

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: CloudWatchMetricAlarmToAwsAccountRelProperties = (
        CloudWatchMetricAlarmToAwsAccountRelProperties()
    )


@dataclass(frozen=True)
class CloudWatchMetricAlarmSchema(CartographyNodeSchema):
    "Represents an `AWSCloudWatchMetricAlarm` node in the AWS graph."

    label: str = "AWSCloudWatchMetricAlarm"
    # DEPRECATED: legacy CloudWatchMetricAlarm node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["CloudWatchMetricAlarm"])
    properties: CloudWatchMetricAlarmNodeProperties = (
        CloudWatchMetricAlarmNodeProperties()
    )
    sub_resource_relationship: CloudWatchMetricAlarmToAWSAccountRel = (
        CloudWatchMetricAlarmToAWSAccountRel()
    )
