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
class PagerDutyIntegrationProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    html_url: PropertyRef = PropertyRef("html_url")
    type: PropertyRef = PropertyRef("type")
    summary: PropertyRef = PropertyRef("summary")
    name: PropertyRef = PropertyRef("name", extra_index=True)
    created_at: PropertyRef = PropertyRef("created_at")


@dataclass(frozen=True)
class PagerDutyIntegrationToVendorProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:PagerDutyVendor)<-[:HAS_VENDOR]-(:PagerDutyIntegration)
class PagerDutyIntegrationToVendorRel(CartographyRelSchema):
    target_node_label: str = "PagerDutyVendor"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("vendor.id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_VENDOR"
    properties: PagerDutyIntegrationToVendorProperties = (
        PagerDutyIntegrationToVendorProperties()
    )


@dataclass(frozen=True)
class PagerDutyIntegrationToServiceProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:PagerDutyService)-[:HAS_INTEGRATION]->(:PagerDutyIntegration)
class PagerDutyIntegrationToServiceRel(CartographyRelSchema):
    target_node_label: str = "PagerDutyService"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("service.id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_INTEGRATION"
    properties: PagerDutyIntegrationToServiceProperties = (
        PagerDutyIntegrationToServiceProperties()
    )


@dataclass(frozen=True)
class PagerDutyIntegrationSchema(CartographyNodeSchema):
    label: str = "PagerDutyIntegration"
    properties: PagerDutyIntegrationProperties = PagerDutyIntegrationProperties()
    scoped_cleanup: bool = False
    other_relationships: OtherRelationships = OtherRelationships(
        [
            PagerDutyIntegrationToVendorRel(),
            PagerDutyIntegrationToServiceRel(),
        ]
    )
