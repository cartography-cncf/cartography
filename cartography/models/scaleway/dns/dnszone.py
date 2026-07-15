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
    id: PropertyRef = PropertyRef(
        "id",
        extra_index=True,
        description="Full zone name (`subdomain.domain` or `domain`).",
    )
    domain: PropertyRef = PropertyRef(
        "domain", extra_index=True, description="Apex domain of the zone."
    )
    subdomain: PropertyRef = PropertyRef(
        "subdomain",
        description="Subdomain within the apex (empty for the apex zone itself).",
    )
    status: PropertyRef = PropertyRef(
        "status", description="Zone status (`active`, `pending`, `error`, ...)."
    )
    message: PropertyRef = PropertyRef(
        "message", description="Status message returned by the API."
    )
    ns: PropertyRef = PropertyRef(
        "ns",
        description="Authoritative name servers currently configured for the zone.",
    )
    ns_default: PropertyRef = PropertyRef(
        "ns_default", description="Default Scaleway name servers."
    )
    ns_master: PropertyRef = PropertyRef(
        "ns_master", description="Master name servers."
    )
    linked_products: PropertyRef = PropertyRef(
        "linked_products", description="Scaleway products linked to this zone."
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="Zone last update date."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Timestamp of the last update"
    )


@dataclass(frozen=True)
class ScalewayDnsZoneToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewayDnsZone)
class ScalewayDnsZoneToProjectRel(CartographyRelSchema):
    """Connects `ScalewayProject` to `ScalewayDnsZone` through `RESOURCE`."""

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
    """Represents a DNS zone managed by Scaleway Domains & DNS. The zone's ID is composed
    from `{subdomain}.{domain}` (or just `{domain}` for apex zones), which is the value
    the Scaleway API itself uses as the zone path parameter.
    """

    label: str = "ScalewayDnsZone"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["DNSZone"])
    properties: ScalewayDnsZoneProperties = ScalewayDnsZoneProperties()
    sub_resource_relationship: ScalewayDnsZoneToProjectRel = (
        ScalewayDnsZoneToProjectRel()
    )
