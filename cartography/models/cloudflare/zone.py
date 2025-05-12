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
    account_id: PropertyRef = PropertyRef('account.id')
    account_name: PropertyRef = PropertyRef('account.name')
    activated_on: PropertyRef = PropertyRef('activated_on')
    created_on: PropertyRef = PropertyRef('created_on')
    development_mode: PropertyRef = PropertyRef('development_mode')
    meta_cdn_only: PropertyRef = PropertyRef('meta.cdn_only')
    meta_custom_certificate_quota: PropertyRef = PropertyRef('meta.custom_certificate_quota')
    meta_dns_only: PropertyRef = PropertyRef('meta.dns_only')
    meta_foundation_dns: PropertyRef = PropertyRef('meta.foundation_dns')
    meta_page_rule_quota: PropertyRef = PropertyRef('meta.page_rule_quota')
    meta_phishing_detected: PropertyRef = PropertyRef('meta.phishing_detected')
    meta_step: PropertyRef = PropertyRef('meta.step')
    modified_on: PropertyRef = PropertyRef('modified_on')
    name: PropertyRef = PropertyRef('name')
    original_dnshost: PropertyRef = PropertyRef('original_dnshost')
    original_registrar: PropertyRef = PropertyRef('original_registrar')
    owner_id: PropertyRef = PropertyRef('owner.id')
    owner_name: PropertyRef = PropertyRef('owner.name')
    owner_type: PropertyRef = PropertyRef('owner.type')
    status: PropertyRef = PropertyRef('status')
    verification_key: PropertyRef = PropertyRef('verification_key')
    id: PropertyRef = PropertyRef('id')
    paused: PropertyRef = PropertyRef('paused')
    type: PropertyRef = PropertyRef('type')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)






@dataclass(frozen=True)
class CloudflareZoneSchema(CartographyNodeSchema):
    label: str = 'CloudflareZone'
    properties: CloudflareZoneNodeProperties = CloudflareZoneNodeProperties()
