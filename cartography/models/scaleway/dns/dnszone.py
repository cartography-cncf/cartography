from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class ScalewayDnsZoneProperties(CartographyNodeProperties):
    # Scaleway DNS zones have no provider-side ID; we compose
    # "<subdomain>.<domain>" (or just "<domain>" when subdomain is empty),
    # matching the value the API itself uses as the {dns_zone} path param.
    id: PropertyRef = PropertyRef("id", extra_index=True)
    domain: PropertyRef = PropertyRef("domain", extra_index=True)
    subdomain: PropertyRef = PropertyRef("subdomain")
    status: PropertyRef = PropertyRef("status")
    message: PropertyRef = PropertyRef("message")
    ns: PropertyRef = PropertyRef("ns")
    ns_default: PropertyRef = PropertyRef("ns_default")
    ns_master: PropertyRef = PropertyRef("ns_master")
    linked_products: PropertyRef = PropertyRef("linked_products")
    updated_at: PropertyRef = PropertyRef("updated_at")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ScalewayDnsZoneToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewayDnsZone)
class ScalewayDnsZoneToProjectRel(CartographyRelSchema):
    target_node_label: str = "ScalewayProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ScalewayDnsZoneToProjectRelProperties = (
        ScalewayDnsZoneToProjectRelProperties()
    )


@dataclass(frozen=True)
class ScalewayDnsZoneSchema(CartographyNodeSchema):
    label: str = "ScalewayDnsZone"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["DNSZone"])
    properties: ScalewayDnsZoneProperties = ScalewayDnsZoneProperties()
    sub_resource_relationship: ScalewayDnsZoneToProjectRel = (
        ScalewayDnsZoneToProjectRel()
    )
