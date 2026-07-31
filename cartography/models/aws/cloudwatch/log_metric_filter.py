from dataclasses import dataclass

from cartography.models.aws.extra_labels import LEGACY_CLOUD_WATCH_LOG_METRIC_FILTER
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
class CloudWatchLogMetricFilterNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Ensures that the id field is a unique combination of logGroupName and filterName",
    )
    arn: PropertyRef = PropertyRef(
        "filterName",
        extra_index=True,
        description="The name of the metric filter. CloudWatch exposes no ARN for metric filters, so the filter name is stored here for query convenience",
    )
    region: PropertyRef = PropertyRef(
        "Region",
        set_in_kwargs=True,
        description="The region of the CloudWatch Log Metric Filter",
    )
    filter_name: PropertyRef = PropertyRef(
        "filterName",
        description="The name of the filter pattern used to extract metric data from log events",
    )
    filter_pattern: PropertyRef = PropertyRef(
        "filterPattern",
        description="The pattern used to extract metric data from CloudWatch log events",
    )
    log_group_name: PropertyRef = PropertyRef(
        "logGroupName",
        description="The name of the log group to which this metric filter is applied",
    )
    metric_name: PropertyRef = PropertyRef(
        "metricName", description="The name of the metric emitted by this filter"
    )
    metric_namespace: PropertyRef = PropertyRef(
        "metricNamespace",
        description="The namespace of the metric emitted by this filter",
    )
    metric_value: PropertyRef = PropertyRef(
        "metricValue",
        description="The value to publish to the CloudWatch metric when a log event matches the filter pattern",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class CloudWatchLogMetricFilterToAwsAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class CloudWatchLogMetricFilterToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: CloudWatchLogMetricFilterToAwsAccountRelProperties = (
        CloudWatchLogMetricFilterToAwsAccountRelProperties()
    )


@dataclass(frozen=True)
class CloudWatchLogMetricFilterToCloudWatchLogGroupRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class CloudWatchLogMetricFilterToCloudWatchLogGroupRel(CartographyRelSchema):
    target_node_label: str = "AWSCloudWatchLogGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"log_group_name": PropertyRef("logGroupName")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "METRIC_FILTER_OF"
    properties: CloudWatchLogMetricFilterToCloudWatchLogGroupRelProperties = (
        CloudWatchLogMetricFilterToCloudWatchLogGroupRelProperties()
    )


@dataclass(frozen=True)
class CloudWatchLogMetricFilterSchema(CartographyNodeSchema):
    """Representation of an AWS [CloudWatch Log Metric Filter](https://docs.aws.amazon.com/AmazonCloudWatchLogs/latest/APIReference/API_DescribeMetricFilters.html)"""

    label: str = "AWSCloudWatchLogMetricFilter"
    # DEPRECATED: legacy CloudWatchLogMetricFilter node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [LEGACY_CLOUD_WATCH_LOG_METRIC_FILTER]
    )
    properties: CloudWatchLogMetricFilterNodeProperties = (
        CloudWatchLogMetricFilterNodeProperties()
    )
    sub_resource_relationship: CloudWatchLogMetricFilterToAWSAccountRel = (
        CloudWatchLogMetricFilterToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            CloudWatchLogMetricFilterToCloudWatchLogGroupRel(),
        ]
    )
