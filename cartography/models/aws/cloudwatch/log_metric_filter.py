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
class CloudWatchLogMetricFilterNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    arn: PropertyRef = PropertyRef("filterName", extra_index=True)
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    filter_name: PropertyRef = PropertyRef("filterName")
    filter_pattern: PropertyRef = PropertyRef("filterPattern")
    log_group_name: PropertyRef = PropertyRef("logGroupName")
    metric_name: PropertyRef = PropertyRef("metricName")
    metric_namespace: PropertyRef = PropertyRef("metricNamespace")
    metric_value: PropertyRef = PropertyRef("metricValue")
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
    target_node_label: str = "CloudWatchLogGroup"
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
    label: str = "CloudWatchLogMetricFilter"
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
