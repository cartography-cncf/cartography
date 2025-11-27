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
class KonnectCertificateNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    cert: PropertyRef = PropertyRef("cert")
    snis: PropertyRef = PropertyRef("snis")
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")
    tags: PropertyRef = PropertyRef("tags")


@dataclass(frozen=True)
class KonnectCertificateToControlPlaneRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KonnectCertificate)-[:RESOURCE]->(:KonnectControlPlane)
class KonnectCertificateToControlPlaneRel(CartographyRelSchema):
    target_node_label: str = "KonnectControlPlane"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("CONTROL_PLANE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RESOURCE"
    properties: KonnectCertificateToControlPlaneRelProperties = (
        KonnectCertificateToControlPlaneRelProperties()
    )


@dataclass(frozen=True)
class KonnectCertificateSchema(CartographyNodeSchema):
    label: str = "KonnectCertificate"
    properties: KonnectCertificateNodeProperties = KonnectCertificateNodeProperties()
    sub_resource_relationship: KonnectCertificateToControlPlaneRel = (
        KonnectCertificateToControlPlaneRel()
    )
