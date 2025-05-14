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
class TailscalePostureIntegrationNodeProperties(CartographyNodeProperties):
    provider: PropertyRef = PropertyRef("provider")
    cloud_id: PropertyRef = PropertyRef("cloudId")
    client_id: PropertyRef = PropertyRef("clientId")
    tenant_id: PropertyRef = PropertyRef("tenantId")
    client_secret: PropertyRef = PropertyRef("clientSecret")
    id: PropertyRef = PropertyRef("id")
    config_updated: PropertyRef = PropertyRef("configUpdated")
    status_last_sync: PropertyRef = PropertyRef("status.lastSync")
    status_error: PropertyRef = PropertyRef("status.error")
    status_provider_host_count: PropertyRef = PropertyRef("status.providerHostCount")
    status_matched_count: PropertyRef = PropertyRef("status.matchedCount")
    status_possible_matched_count: PropertyRef = PropertyRef(
        "status.possibleMatchedCount"
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class TailscalePostureIntegrationSchema(CartographyNodeSchema):
    label: str = "TailscalePostureIntegration"
    properties: TailscalePostureIntegrationNodeProperties = (
        TailscalePostureIntegrationNodeProperties()
    )
