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
class CloudWatchMetricAlarmNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("AlarmArn")
    arn: PropertyRef = PropertyRef("AlarmArn", extra_index=True)
    alarm_name: PropertyRef = PropertyRef("AlarmName")
    alarm_description: PropertyRef = PropertyRef("AlarmDescription")
    state_value: PropertyRef = PropertyRef("StateValue")
    state_reason: PropertyRef = PropertyRef("StateReason")
    actions_enabled: PropertyRef = PropertyRef("ActionsEnabled")
    comparison_operator: PropertyRef = PropertyRef("ComparisonOperator")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class CloudWatchMetricAlarmToAwsAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class CloudWatchMetricAlarmToAWSAccountRel(CartographyRelSchema):
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
    label: str = "CloudWatchMetricAlarm"
    properties: CloudWatchMetricAlarmNodeProperties = (
        CloudWatchMetricAlarmNodeProperties()
    )
    sub_resource_relationship: CloudWatchMetricAlarmToAWSAccountRel = (
        CloudWatchMetricAlarmToAWSAccountRel()
    )
