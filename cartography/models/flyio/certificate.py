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
from cartography.models.ontology.labels import CERTIFICATE


@dataclass(frozen=True)
class FlyCertificateNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Synthesized `<app_id>/<hostname>` key."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    hostname: PropertyRef = PropertyRef(
        "hostname", extra_index=True, description="Certificate hostname."
    )
    status: PropertyRef = PropertyRef("status", description="Certificate status.")
    dns_provider: PropertyRef = PropertyRef(
        "dns_provider", description="DNS provider detected by Fly.io."
    )
    configured: PropertyRef = PropertyRef(
        "configured", description="Whether the certificate is configured."
    )
    acme_dns_configured: PropertyRef = PropertyRef(
        "acme_dns_configured",
        description="Whether ACME DNS validation is configured.",
    )
    acme_alpn_configured: PropertyRef = PropertyRef(
        "acme_alpn_configured",
        description="Whether ACME ALPN validation is configured.",
    )
    acme_http_configured: PropertyRef = PropertyRef(
        "acme_http_configured",
        description="Whether ACME HTTP validation is configured.",
    )
    ownership_txt_configured: PropertyRef = PropertyRef(
        "ownership_txt_configured",
        description="Whether Fly ownership TXT validation is configured.",
    )
    acme_requested: PropertyRef = PropertyRef(
        "acme_requested", description="Whether an ACME certificate was requested."
    )
    has_custom_certificate: PropertyRef = PropertyRef(
        "has_custom_certificate", description="Whether a custom certificate exists."
    )
    has_fly_certificate: PropertyRef = PropertyRef(
        "has_fly_certificate",
        description="Whether a Fly-managed certificate exists.",
    )
    certificate_authorities: PropertyRef = PropertyRef(
        "certificate_authorities",
        description="Certificate authorities from nested issued certificate metadata.",
    )
    sources: PropertyRef = PropertyRef(
        "sources", description="Certificate sources from nested certificate metadata."
    )
    issuers: PropertyRef = PropertyRef(
        "issuers", description="Certificate issuers from nested certificate metadata."
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Creation timestamp."
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="Last update timestamp."
    )
    app_id: PropertyRef = PropertyRef("APP_ID", set_in_kwargs=True)


@dataclass(frozen=True)
class FlyCertificateToAppRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:FlyApp)-[:RESOURCE]->(:FlyCertificate)
class FlyCertificateToAppRel(CartographyRelSchema):
    """Connects `FlyApp` to `FlyCertificate` through `RESOURCE`."""

    target_node_label: str = "FlyApp"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("APP_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: FlyCertificateToAppRelProperties = FlyCertificateToAppRelProperties()


@dataclass(frozen=True)
class FlyCertificateSchema(CartographyNodeSchema):
    """Represents a Fly.io certificate or custom hostname."""

    label: str = "FlyCertificate"
    properties: FlyCertificateNodeProperties = FlyCertificateNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([CERTIFICATE])
    sub_resource_relationship: FlyCertificateToAppRel = FlyCertificateToAppRel()
