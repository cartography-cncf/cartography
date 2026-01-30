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
class CloudflareZoneNodeProperties(CartographyNodeProperties):
    activated_on: PropertyRef = PropertyRef("activated_on")
    created_on: PropertyRef = PropertyRef("created_on")
    development_mode: PropertyRef = PropertyRef("development_mode")
    cdn_only: PropertyRef = PropertyRef("meta.cdn_only")
    custom_certificate_quota: PropertyRef = PropertyRef("meta.custom_certificate_quota")
    dns_only: PropertyRef = PropertyRef("meta.dns_only")
    foundation_dns: PropertyRef = PropertyRef("meta.foundation_dns")
    page_rule_quota: PropertyRef = PropertyRef("meta.page_rule_quota")
    phishing_detected: PropertyRef = PropertyRef("meta.phishing_detected")
    modified_on: PropertyRef = PropertyRef("modified_on")
    name: PropertyRef = PropertyRef("name")
    original_dnshost: PropertyRef = PropertyRef("original_dnshost")
    original_registrar: PropertyRef = PropertyRef("original_registrar")
    status: PropertyRef = PropertyRef("status")
    verification_key: PropertyRef = PropertyRef("verification_key")
    id: PropertyRef = PropertyRef("id")
    paused: PropertyRef = PropertyRef("paused")
    type: PropertyRef = PropertyRef("type")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class CloudflareZoneToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:CloudflareZone)<-[:RESOURCE]-(:CloudflareAccount)
class CloudflareZoneToAccountRel(CartographyRelSchema):
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
    label: str = "CloudflareZone"
    properties: CloudflareZoneNodeProperties = CloudflareZoneNodeProperties()
    sub_resource_relationship: CloudflareZoneToAccountRel = CloudflareZoneToAccountRel()
