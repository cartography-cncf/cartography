from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties, CartographyNodeSchema
from cartography.models.core.relationships import (
    CartographyRelProperties,
    CartographyRelSchema,
    LinkDirection,
    make_target_node_matcher,
    TargetNodeMatcher,
)

@dataclass(frozen=True)
class CloudWatchLogMetricFilterNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("filterName")  # Use unique filter name per group
    filter_name: PropertyRef = PropertyRef("filterName", extra_index=True)
    filter_pattern: PropertyRef = PropertyRef("filterPattern")
    creation_time: PropertyRef = PropertyRef("creationTime")
    metric_name: PropertyRef = PropertyRef("metricTransformations[0].metricName")
    metric_namespace: PropertyRef = PropertyRef("metricTransformations[0].metricNamespace")
    metric_value: PropertyRef = PropertyRef("metricTransformations[0].metricValue")
    log_group_name: PropertyRef = PropertyRef("logGroupName")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)

@dataclass(frozen=True)
class LogMetricFilterToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)

@dataclass(frozen=True)
class LogMetricFilterToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: LogMetricFilterToAWSAccountRelProperties = LogMetricFilterToAWSAccountRelProperties()

@dataclass(frozen=True)
class CloudWatchLogMetricFilterSchema(CartographyNodeSchema):
    label: str = "CloudWatchLogMetricFilter"
    properties: CloudWatchLogMetricFilterNodeProperties = CloudWatchLogMetricFilterNodeProperties()
    sub_resource_relationship: LogMetricFilterToAWSAccountRel = LogMetricFilterToAWSAccountRel()
