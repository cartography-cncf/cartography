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
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    provider: PropertyRef = PropertyRef("provider")
    cloud_id: PropertyRef = PropertyRef("cloudId")
    client_id: PropertyRef = PropertyRef("clientId")
    tenant_id: PropertyRef = PropertyRef("tenantId")
    config_updated: PropertyRef = PropertyRef("configUpdated")
    status_last_sync: PropertyRef = PropertyRef("status.lastSync")
    status_error: PropertyRef = PropertyRef("status.error")
    status_provider_host_count: PropertyRef = PropertyRef("status.providerHostCount")
    status_matched_count: PropertyRef = PropertyRef("status.matchedCount")
    status_possible_matched_count: PropertyRef = PropertyRef(
        "status.possibleMatchedCount"
    )


@dataclass(frozen=True)
class TailscalePostureIntegrationToTailnetRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:TailscaleTailnet)-[:RESOURCE]->(:TailscalePostureIntegration)
class TailscalePostureIntegrationToTailnetRel(CartographyRelSchema):
    target_node_label: str = "TailscaleTailnet"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("org", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: TailscalePostureIntegrationToTailnetRelProperties = (
        TailscalePostureIntegrationToTailnetRelProperties()
    )


@dataclass(frozen=True)
class TailscalePostureIntegrationSchema(CartographyNodeSchema):
    label: str = "TailscalePostureIntegration"
    properties: TailscalePostureIntegrationNodeProperties = (
        TailscalePostureIntegrationNodeProperties()
    )
    sub_resource_relationship: TailscalePostureIntegrationToTailnetRel = (
        TailscalePostureIntegrationToTailnetRel()
    )
