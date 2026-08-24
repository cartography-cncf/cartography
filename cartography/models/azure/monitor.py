import logging
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

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AzureMonitorMetricAlertProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Azure Resource Manager ID of the metric alert.",
    )
    name: PropertyRef = PropertyRef(
        "name",
        description="Name of the metric alert.",
    )
    location: PropertyRef = PropertyRef(
        "location",
        description="Azure location assigned to the metric alert.",
    )
    description: PropertyRef = PropertyRef(
        "description",
        description="Description of the metric alert.",
    )
    severity: PropertyRef = PropertyRef(
        "severity",
        description="Severity level of the metric alert.",
    )
    enabled: PropertyRef = PropertyRef(
        "enabled",
        description="Whether the metric alert is enabled.",
    )
    window_size: PropertyRef = PropertyRef(
        "window_size",
        description="Time window over which the alert criteria are evaluated.",
    )
    evaluation_frequency: PropertyRef = PropertyRef(
        "evaluation_frequency",
        description="Frequency at which the alert criteria are evaluated.",
    )
    last_updated_time: PropertyRef = PropertyRef(
        "last_updated_time",
        description="Timestamp when the metric alert was last updated.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureSubscriptionToMetricAlertRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureSubscriptionToMetricAlertRel(CartographyRelSchema):
    """An Azure subscription contains the metric alert as a resource."""

    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureSubscriptionToMetricAlertRelProperties = (
        AzureSubscriptionToMetricAlertRelProperties()
    )


@dataclass(frozen=True)
# (:AzureMonitorMetricAlert)<-[:HAS_METRIC_ALERT]-(:AzureSubscription) - Backwards compatibility
class AzureSubscriptionToMetricAlertDeprecatedRel(CartographyRelSchema):
    """Deprecated compatibility edge linking a subscription to a metric alert."""

    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_METRIC_ALERT"
    properties: AzureSubscriptionToMetricAlertRelProperties = (
        AzureSubscriptionToMetricAlertRelProperties()
    )


@dataclass(frozen=True)
class AzureMonitorMetricAlertSchema(CartographyNodeSchema):
    """An Azure Monitor alert that evaluates metric-based criteria."""

    label: str = "AzureMonitorMetricAlert"
    properties: AzureMonitorMetricAlertProperties = AzureMonitorMetricAlertProperties()
    sub_resource_relationship: AzureSubscriptionToMetricAlertRel = (
        AzureSubscriptionToMetricAlertRel()
    )
    # DEPRECATED: for backward compatibility, will be removed in v1.0.0
    other_relationships: OtherRelationships = OtherRelationships(
        rels=[AzureSubscriptionToMetricAlertDeprecatedRel()],
    )
