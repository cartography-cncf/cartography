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
from cartography.models.ontology.labels import CERTIFICATE


# --- Node Definitions ---
@dataclass(frozen=True)
class NetlifyCertificateNodeProperties(CartographyNodeProperties):
    # `<site_id>_ssl`, built in transform(). Netlify's TLS endpoint returns a certificate with no
    # identifier of any kind, and a site has at most one, so the site scopes it. Note that
    # nothing time-varying goes into the id: folding `expires_at` in would give the node a new
    # identity on every renewal and defeat cleanup.
    id: PropertyRef = PropertyRef(
        "id",
        description="`<site_id>_ssl`. Netlify's TLS endpoint returns a certificate with no identifier of any kind, and a site has at most one. Nothing time-varying goes into the id: folding `expires_at` in would give the node a new identity on every renewal and defeat cleanup.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    site_id: PropertyRef = PropertyRef(
        "site_id", description="Id of the site the certificate serves."
    )
    # The primary domain, taken as the first entry of `domains` to satisfy the Certificate
    # ontology mapping's required `domain` field. The full SAN list stays in `domains`.
    domain: PropertyRef = PropertyRef(
        "domain",
        extra_index=True,
        description="Primary domain, the first entry of `domains`.",
    )
    domains: PropertyRef = PropertyRef(
        "domains", description="Every domain the certificate covers."
    )
    state: PropertyRef = PropertyRef(
        "state", description="Certificate state, e.g. `issued`, `provisioning`."
    )
    expires_at: PropertyRef = PropertyRef(
        "expires_at", description="When the certificate expires."
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="When the certificate was issued."
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="When the certificate was last renewed."
    )


# --- Relationship Definitions ---
@dataclass(frozen=True)
class NetlifyCertificateToNetlifyAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:NetlifyAccount)-[:RESOURCE]->(:NetlifyCertificate)
class NetlifyCertificateToNetlifyAccountRel(CartographyRelSchema):
    target_node_label: str = "NetlifyAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("NETLIFY_ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: NetlifyCertificateToNetlifyAccountRelProperties = (
        NetlifyCertificateToNetlifyAccountRelProperties()
    )


@dataclass(frozen=True)
class NetlifyCertificateToSiteRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:NetlifySite)-[:HAS_CERTIFICATE]->(:NetlifyCertificate)
class NetlifyCertificateToSiteRel(CartographyRelSchema):
    target_node_label: str = "NetlifySite"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("site_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_CERTIFICATE"
    properties: NetlifyCertificateToSiteRelProperties = (
        NetlifyCertificateToSiteRelProperties()
    )


# --- Main Schema ---
@dataclass(frozen=True)
class NetlifyCertificateSchema(CartographyNodeSchema):
    """
    The TLS certificate serving a Netlify site's custom domains.
    """

    label: str = "NetlifyCertificate"
    properties: NetlifyCertificateNodeProperties = NetlifyCertificateNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([CERTIFICATE])
    sub_resource_relationship: NetlifyCertificateToNetlifyAccountRel = (
        NetlifyCertificateToNetlifyAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [NetlifyCertificateToSiteRel()],
    )
