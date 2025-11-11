import logging
from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AzureMonitorMetricAlertProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    location: PropertyRef = PropertyRef("location")
    description: PropertyRef = PropertyRef("description")
    severity: PropertyRef = PropertyRef("severity")
    enabled: PropertyRef = PropertyRef("enabled")
    window_size: PropertyRef = PropertyRef("window_size")
    evaluation_frequency: PropertyRef = PropertyRef("evaluation_frequency")
    last_updated_time: PropertyRef = PropertyRef("last_updated_time")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureSubscriptionToMetricAlertRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureSubscriptionToMetricAlertRel(CartographyRelSchema):
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
    label: str = "AzureMonitorMetricAlert"
    properties: AzureMonitorMetricAlertProperties = AzureMonitorMetricAlertProperties()
    sub_resource_relationship: AzureSubscriptionToMetricAlertRel = (
        AzureSubscriptionToMetricAlertRel()
    )
