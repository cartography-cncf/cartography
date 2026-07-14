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
class CloudflareZoneNodeProperties(CartographyNodeProperties):
    activated_on: PropertyRef = PropertyRef(
        "activated_on",
        description="Timestamp when ownership was verified and the zone became active.",
    )
    created_on: PropertyRef = PropertyRef(
        "created_on",
        description="Timestamp when the zone was created.",
    )
    development_mode: PropertyRef = PropertyRef(
        "development_mode",
        description="Seconds until development mode expires, or since it expired.",
    )
    cdn_only: PropertyRef = PropertyRef(
        "meta.cdn_only",
        description="Whether the zone is configured only for CDN.",
    )
    custom_certificate_quota: PropertyRef = PropertyRef(
        "meta.custom_certificate_quota",
        description="Number of custom certificates allowed for the zone.",
    )
    dns_only: PropertyRef = PropertyRef(
        "meta.dns_only",
        description="Whether the zone is configured only for DNS.",
    )
    foundation_dns: PropertyRef = PropertyRef(
        "meta.foundation_dns",
        description="Whether the zone uses Foundation DNS.",
    )
    page_rule_quota: PropertyRef = PropertyRef(
        "meta.page_rule_quota",
        description="Number of page rules allowed for the zone.",
    )
    phishing_detected: PropertyRef = PropertyRef(
        "meta.phishing_detected",
        description="Whether the zone was flagged for phishing.",
    )
    modified_on: PropertyRef = PropertyRef(
        "modified_on",
        description="Timestamp when the zone was last modified.",
    )
    name: PropertyRef = PropertyRef("name", description="Domain name.")
    original_dnshost: PropertyRef = PropertyRef(
        "original_dnshost",
        description="DNS host used before switching to Cloudflare.",
    )
    original_registrar: PropertyRef = PropertyRef(
        "original_registrar",
        description="Registrar used before switching to Cloudflare.",
    )
    status: PropertyRef = PropertyRef("status", description="Cloudflare zone status.")
    verification_key: PropertyRef = PropertyRef(
        "verification_key",
        description="Verification key for partial zone setup.",
    )
    id: PropertyRef = PropertyRef("id", description="Cloudflare zone ID.")
    paused: PropertyRef = PropertyRef(
        "paused",
        description="Whether the zone only uses Cloudflare DNS services.",
    )
    type: PropertyRef = PropertyRef(
        "type",
        description="Zone type, such as full or partial.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last update.",
    )


@dataclass(frozen=True)
class CloudflareZoneToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:CloudflareZone)<-[:RESOURCE]-(:CloudflareAccount)
class CloudflareZoneToAccountRel(CartographyRelSchema):
    """The account contains the DNS zone."""

    target_node_label: str = "CloudflareAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("account_id", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: CloudflareZoneToAccountRelProperties = (
        CloudflareZoneToAccountRelProperties()
    )


@dataclass(frozen=True)
class CloudflareZoneSchema(CartographyNodeSchema):
    """A DNS zone managed by Cloudflare."""

    label: str = "CloudflareZone"
    properties: CloudflareZoneNodeProperties = CloudflareZoneNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["DNSZone"])
    sub_resource_relationship: CloudflareZoneToAccountRel = CloudflareZoneToAccountRel()
