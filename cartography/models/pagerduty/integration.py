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
    id: PropertyRef = PropertyRef("id", description="Integration ID.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Timestamp of the last update."
    )
    html_url: PropertyRef = PropertyRef(
        "html_url", description="PagerDuty web URL for the integration."
    )
    type: PropertyRef = PropertyRef(
        "type", description="PagerDuty object type for the integration."
    )
    summary: PropertyRef = PropertyRef(
        "summary", description="Short summary of the integration."
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Integration name."
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Timestamp when the integration was created."
    )


@dataclass(frozen=True)
class PagerDutyIntegrationToVendorRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:PagerDutyVendor)<-[:HAS_VENDOR]-(:PagerDutyIntegration)
class PagerDutyIntegrationToVendorRel(CartographyRelSchema):
    """The vendor provided by an integration."""

    target_node_label: str = "PagerDutyVendor"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("vendor.id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_VENDOR"
    properties: PagerDutyIntegrationToVendorRelProperties = (
        PagerDutyIntegrationToVendorRelProperties()
    )


@dataclass(frozen=True)
class PagerDutyIntegrationToServiceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:PagerDutyService)-[:HAS_INTEGRATION]->(:PagerDutyIntegration)
class PagerDutyIntegrationToServiceRel(CartographyRelSchema):
    """The service that contains an integration."""

    target_node_label: str = "PagerDutyService"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("service.id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_INTEGRATION"
    properties: PagerDutyIntegrationToServiceRelProperties = (
        PagerDutyIntegrationToServiceRelProperties()
    )


@dataclass(frozen=True)
class PagerDutyIntegrationSchema(CartographyNodeSchema):
    """A PagerDuty integration configured on a service."""

    label: str = "PagerDutyIntegration"
    properties: PagerDutyIntegrationProperties = PagerDutyIntegrationProperties()
    scoped_cleanup: bool = False
    other_relationships: OtherRelationships = OtherRelationships(
        [
            PagerDutyIntegrationToVendorRel(),
            PagerDutyIntegrationToServiceRel(),
        ]
    )
