from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.ontology.labels import COMPUTE_SERVICE


@dataclass(frozen=True)
class ScalewayWebHostingProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="ID of the Web Hosting account.")
    status: PropertyRef = PropertyRef(
        "status", description="Status of the Web Hosting account."
    )
    offer_name: PropertyRef = PropertyRef(
        "offer_name", description="Name of the selected Web Hosting offer."
    )
    region: PropertyRef = PropertyRef(
        "region", description="Region the Web Hosting account lives in."
    )
    domain: PropertyRef = PropertyRef(
        "domain", description="Domain name served by the Web Hosting account."
    )
    dns_status: PropertyRef = PropertyRef(
        "dns_status", description="DNS validation status for the served domain."
    )
    domain_status: PropertyRef = PropertyRef(
        "domain_status", description="Domain validation status for the hosting account."
    )
    protected: PropertyRef = PropertyRef(
        "protected", description="Whether protection is enabled for the account."
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Creation timestamp."
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="Last update timestamp."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ScalewayWebHostingToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewayWebHosting)
class ScalewayWebHostingToProjectRel(CartographyRelSchema):
    """Connects `ScalewayProject` to `ScalewayWebHosting` through `RESOURCE`."""

    target_node_label: str = "ScalewayProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ScalewayWebHostingToProjectRelProperties = (
        ScalewayWebHostingToProjectRelProperties()
    )


@dataclass(frozen=True)
class ScalewayWebHostingToRegisteredDomainRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayWebHosting)-[:EXPOSE]->(:ScalewayRegisteredDomain)
class ScalewayWebHostingToRegisteredDomainRel(CartographyRelSchema):
    """Identifies the registered Scaleway domain served by the hosting account."""

    target_node_label: str = "ScalewayRegisteredDomain"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("domain")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "EXPOSE"
    properties: ScalewayWebHostingToRegisteredDomainRelProperties = (
        ScalewayWebHostingToRegisteredDomainRelProperties()
    )


@dataclass(frozen=True)
class ScalewayWebHostingToDnsZoneRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayWebHosting)-[:EXPOSE]->(:ScalewayDnsZone)
class ScalewayWebHostingToDnsZoneRel(CartographyRelSchema):
    """Identifies the Scaleway DNS zone served by the hosting account."""

    target_node_label: str = "ScalewayDnsZone"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("domain")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "EXPOSE"
    properties: ScalewayWebHostingToDnsZoneRelProperties = (
        ScalewayWebHostingToDnsZoneRelProperties()
    )


@dataclass(frozen=True)
class ScalewayWebHostingSchema(CartographyNodeSchema):
    """Represents a Web Hosting account in Scaleway."""

    label: str = "ScalewayWebHosting"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([COMPUTE_SERVICE])
    properties: ScalewayWebHostingProperties = ScalewayWebHostingProperties()
    sub_resource_relationship: ScalewayWebHostingToProjectRel = (
        ScalewayWebHostingToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ScalewayWebHostingToRegisteredDomainRel(),
            ScalewayWebHostingToDnsZoneRel(),
        ]
    )
