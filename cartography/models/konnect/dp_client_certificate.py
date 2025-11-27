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
class KonnectDPClientCertificateNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    cert: PropertyRef = PropertyRef("cert")
    created_at: PropertyRef = PropertyRef("created_at")


@dataclass(frozen=True)
class KonnectDPClientCertificateToControlPlaneRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KonnectDPClientCertificate)-[:RESOURCE]->(:KonnectControlPlane)
class KonnectDPClientCertificateToControlPlaneRel(CartographyRelSchema):
    target_node_label: str = "KonnectControlPlane"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("CONTROL_PLANE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RESOURCE"
    properties: KonnectDPClientCertificateToControlPlaneRelProperties = (
        KonnectDPClientCertificateToControlPlaneRelProperties()
    )


@dataclass(frozen=True)
class KonnectDPClientCertificateSchema(CartographyNodeSchema):
    label: str = "KonnectDPClientCertificate"
    properties: KonnectDPClientCertificateNodeProperties = (
        KonnectDPClientCertificateNodeProperties()
    )
    sub_resource_relationship: KonnectDPClientCertificateToControlPlaneRel = (
        KonnectDPClientCertificateToControlPlaneRel()
    )
