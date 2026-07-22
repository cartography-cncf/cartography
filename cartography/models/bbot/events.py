from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_source_node_matcher
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import SourceNodeMatcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class BbotNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    bbot_ids: PropertyRef = PropertyRef("bbot_ids")
    event_type: PropertyRef = PropertyRef("event_type")
    data: PropertyRef = PropertyRef("data")
    name: PropertyRef = PropertyRef("name")
    host: PropertyRef = PropertyRef("host")
    port: PropertyRef = PropertyRef("port")
    url: PropertyRef = PropertyRef("url")
    ip_address: PropertyRef = PropertyRef("ip_address", extra_index=True)
    is_global: PropertyRef = PropertyRef("is_global")
    network: PropertyRef = PropertyRef("network")
    endpoint: PropertyRef = PropertyRef("endpoint")
    asn: PropertyRef = PropertyRef("asn")
    country: PropertyRef = PropertyRef("country")
    subnet: PropertyRef = PropertyRef("subnet")
    technology: PropertyRef = PropertyRef("technology")
    email: PropertyRef = PropertyRef("email")
    organization: PropertyRef = PropertyRef("organization")
    platform: PropertyRef = PropertyRef("platform")
    profile_name: PropertyRef = PropertyRef("profile_name")
    bucket_provider: PropertyRef = PropertyRef("bucket_provider")
    bucket_name: PropertyRef = PropertyRef("bucket_name")
    finding_name: PropertyRef = PropertyRef("finding_name")
    severity: PropertyRef = PropertyRef("severity")
    confidence: PropertyRef = PropertyRef("confidence")
    description: PropertyRef = PropertyRef("description")
    cves: PropertyRef = PropertyRef("cves")
    status: PropertyRef = PropertyRef("status")
    started_at: PropertyRef = PropertyRef("started_at")
    finished_at: PropertyRef = PropertyRef("finished_at")
    duration_seconds: PropertyRef = PropertyRef("duration_seconds")
    targets: PropertyRef = PropertyRef("targets")
    scan_id: PropertyRef = PropertyRef("scan_id")
    occurrence_uuids: PropertyRef = PropertyRef("occurrence_uuids")
    occurrence_count: PropertyRef = PropertyRef("occurrence_count")
    parent_uuids: PropertyRef = PropertyRef("parent_uuids")
    tags: PropertyRef = PropertyRef("tags")
    modules: PropertyRef = PropertyRef("modules")
    resolved_hosts: PropertyRef = PropertyRef("resolved_hosts")
    discovery_contexts: PropertyRef = PropertyRef("discovery_contexts")
    scope_distance: PropertyRef = PropertyRef("scope_distance")
    web_spider_distance: PropertyRef = PropertyRef("web_spider_distance")
    observed_at: PropertyRef = PropertyRef("observed_at")
    source_uri: PropertyRef = PropertyRef("source_uri")


@dataclass(frozen=True)
class BbotScanSchema(CartographyNodeSchema):
    label: str = "BbotScan"
    scoped_cleanup: bool = False
    properties: BbotNodeProperties = BbotNodeProperties()


@dataclass(frozen=True)
class BbotDNSNameSchema(CartographyNodeSchema):
    label: str = "BbotDNSName"
    scoped_cleanup: bool = False
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["DNSRecord"])
    properties: BbotNodeProperties = BbotNodeProperties()


@dataclass(frozen=True)
class BbotIPAddressSchema(CartographyNodeSchema):
    label: str = "BbotIPAddress"
    scoped_cleanup: bool = False
    properties: BbotNodeProperties = BbotNodeProperties()


@dataclass(frozen=True)
class BbotIPRangeSchema(CartographyNodeSchema):
    label: str = "BbotIPRange"
    scoped_cleanup: bool = False
    properties: BbotNodeProperties = BbotNodeProperties()


@dataclass(frozen=True)
class BbotOpenTCPPortSchema(CartographyNodeSchema):
    label: str = "BbotOpenTCPPort"
    scoped_cleanup: bool = False
    properties: BbotNodeProperties = BbotNodeProperties()


@dataclass(frozen=True)
class BbotURLSchema(CartographyNodeSchema):
    label: str = "BbotURL"
    scoped_cleanup: bool = False
    properties: BbotNodeProperties = BbotNodeProperties()


@dataclass(frozen=True)
class BbotASNSchema(CartographyNodeSchema):
    label: str = "BbotASN"
    scoped_cleanup: bool = False
    properties: BbotNodeProperties = BbotNodeProperties()


@dataclass(frozen=True)
class BbotTechnologySchema(CartographyNodeSchema):
    label: str = "BbotTechnology"
    scoped_cleanup: bool = False
    properties: BbotNodeProperties = BbotNodeProperties()


@dataclass(frozen=True)
class BbotEmailAddressSchema(CartographyNodeSchema):
    label: str = "BbotEmailAddress"
    scoped_cleanup: bool = False
    properties: BbotNodeProperties = BbotNodeProperties()


@dataclass(frozen=True)
class BbotOrgStubSchema(CartographyNodeSchema):
    label: str = "BbotOrgStub"
    scoped_cleanup: bool = False
    properties: BbotNodeProperties = BbotNodeProperties()


@dataclass(frozen=True)
class BbotSocialSchema(CartographyNodeSchema):
    label: str = "BbotSocial"
    scoped_cleanup: bool = False
    properties: BbotNodeProperties = BbotNodeProperties()


@dataclass(frozen=True)
class BbotStorageBucketSchema(CartographyNodeSchema):
    label: str = "BbotStorageBucket"
    scoped_cleanup: bool = False
    properties: BbotNodeProperties = BbotNodeProperties()


@dataclass(frozen=True)
class BbotFindingSchema(CartographyNodeSchema):
    label: str = "BbotFinding"
    scoped_cleanup: bool = False
    properties: BbotNodeProperties = BbotNodeProperties()


BBOT_SCHEMAS: dict[str, CartographyNodeSchema] = {
    "SCAN": BbotScanSchema(),
    "DNS_NAME": BbotDNSNameSchema(),
    "IP_ADDRESS": BbotIPAddressSchema(),
    "IP_RANGE": BbotIPRangeSchema(),
    "OPEN_TCP_PORT": BbotOpenTCPPortSchema(),
    "URL": BbotURLSchema(),
    "ASN": BbotASNSchema(),
    "TECHNOLOGY": BbotTechnologySchema(),
    "EMAIL_ADDRESS": BbotEmailAddressSchema(),
    "ORG_STUB": BbotOrgStubSchema(),
    "SOCIAL": BbotSocialSchema(),
    "STORAGE_BUCKET": BbotStorageBucketSchema(),
    "FINDING": BbotFindingSchema(),
}


@dataclass(frozen=True)
class BbotMatchLinkProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label",
        set_in_kwargs=True,
    )
    _sub_resource_id: PropertyRef = PropertyRef(
        "_sub_resource_id",
        set_in_kwargs=True,
    )


@dataclass(frozen=True)
class BbotMatchLink(CartographyRelSchema):
    _source_label: str
    _target_label: str
    _relationship_label: str
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("source_id")},
    )
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("target_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    properties: BbotMatchLinkProperties = BbotMatchLinkProperties()

    @property
    def source_node_label(self) -> str:
        return self._source_label

    @property
    def target_node_label(self) -> str:
        return self._target_label

    @property
    def rel_label(self) -> str:
        return self._relationship_label


@dataclass(frozen=True)
class BbotCleanupObservedInRel(CartographyRelSchema):
    """Cleanup-only relationship that enables GraphJob node cleanup."""

    target_node_label: str = "BbotScan"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("_unused_cleanup_matcher")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "OBSERVED_IN"
    properties: BbotMatchLinkProperties = BbotMatchLinkProperties()


@dataclass(frozen=True)
class BbotCleanupSchema(CartographyNodeSchema):
    """Dynamic cleanup schema for each concrete BBOT node label."""

    _node_label: str = "BbotScan"
    scoped_cleanup: bool = False
    properties: BbotNodeProperties = BbotNodeProperties()
    other_relationships: OtherRelationships = OtherRelationships(
        [BbotCleanupObservedInRel()],
    )

    @property
    def label(self) -> str:
        return self._node_label
