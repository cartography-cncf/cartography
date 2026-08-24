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
from cartography.models.ontology.labels import DNS_RECORD
from cartography.models.ontology.labels import SECURITY_ISSUE


@dataclass(frozen=True)
class BbotNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Stable identity derived from the event's normalized deduplication data.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    bbot_ids: PropertyRef = PropertyRef(
        "bbot_ids",
        description="BBOT deduplication IDs represented by this aggregated node.",
    )
    event_type: PropertyRef = PropertyRef(
        "event_type",
        description="Original BBOT event type.",
    )
    data: PropertyRef = PropertyRef(
        "data",
        description="Original event data, serialized when structured.",
    )
    name: PropertyRef = PropertyRef(
        "name",
        description="Normalized event-specific display name, when present.",
    )
    host: PropertyRef = PropertyRef(
        "host",
        description="Normalized hostname or IP address, when present.",
    )
    port: PropertyRef = PropertyRef(
        "port",
        description="Effective TCP port, when present.",
    )
    url: PropertyRef = PropertyRef(
        "url",
        description="Canonical URL, when present.",
    )
    ip_address: PropertyRef = PropertyRef(
        "ip_address",
        extra_index=True,
        description="Canonical IPv4 or IPv6 address.",
    )
    public_ip_address: PropertyRef = PropertyRef(
        "public_ip_address",
        description="Canonical IP address when globally routable.",
    )
    is_global: PropertyRef = PropertyRef(
        "is_global",
        description="Whether the IP address is globally routable.",
    )
    network: PropertyRef = PropertyRef(
        "network",
        description="Canonical IP network in CIDR notation.",
    )
    endpoint: PropertyRef = PropertyRef(
        "endpoint",
        description="BBOT endpoint display value.",
    )
    asn: PropertyRef = PropertyRef(
        "asn",
        description="Autonomous system number.",
    )
    country: PropertyRef = PropertyRef(
        "country",
        description="Country code reported for the autonomous system.",
    )
    subnet: PropertyRef = PropertyRef(
        "subnet",
        description="Network associated with the autonomous system.",
    )
    technology: PropertyRef = PropertyRef(
        "technology",
        description="Normalized detected technology name.",
    )
    email: PropertyRef = PropertyRef(
        "email",
        description="Normalized email address.",
    )
    organization: PropertyRef = PropertyRef(
        "organization",
        description="Normalized organization stub.",
    )
    platform: PropertyRef = PropertyRef(
        "platform",
        description="Social profile platform.",
    )
    profile_name: PropertyRef = PropertyRef(
        "profile_name",
        description="Social profile name.",
    )
    bucket_provider: PropertyRef = PropertyRef(
        "bucket_provider",
        description="Normalized object storage provider.",
    )
    bucket_name: PropertyRef = PropertyRef(
        "bucket_name",
        description="Normalized object storage bucket name.",
    )
    finding_name: PropertyRef = PropertyRef(
        "finding_name",
        description="Stable finding name, when reported.",
    )
    severity: PropertyRef = PropertyRef(
        "severity",
        description="Finding severity reported by BBOT.",
    )
    confidence: PropertyRef = PropertyRef(
        "confidence",
        description="Finding confidence reported by BBOT.",
    )
    description: PropertyRef = PropertyRef(
        "description",
        description="Event-specific explanatory text.",
    )
    cves: PropertyRef = PropertyRef(
        "cves",
        description="CVE identifiers associated with a finding.",
    )
    status: PropertyRef = PropertyRef(
        "status",
        description="BBOT scan status.",
    )
    started_at: PropertyRef = PropertyRef(
        "started_at",
        description="BBOT scan start time.",
    )
    finished_at: PropertyRef = PropertyRef(
        "finished_at",
        description="BBOT scan completion time.",
    )
    duration_seconds: PropertyRef = PropertyRef(
        "duration_seconds",
        description="BBOT scan duration in seconds.",
    )
    targets: PropertyRef = PropertyRef(
        "targets",
        description="Seed targets supplied to the BBOT scan.",
    )
    scan_id: PropertyRef = PropertyRef(
        "scan_id",
        description="BBOT ID of the selected scan containing this observation.",
    )
    occurrence_uuids: PropertyRef = PropertyRef(
        "occurrence_uuids",
        description="Occurrence UUIDs aggregated into this node for the selected scan.",
    )
    occurrence_count: PropertyRef = PropertyRef(
        "occurrence_count",
        description="Number of occurrences aggregated for the selected scan.",
    )
    parent_uuids: PropertyRef = PropertyRef(
        "parent_uuids",
        description="Parent occurrence UUIDs observed in the selected scan.",
    )
    tags: PropertyRef = PropertyRef(
        "tags",
        description="Union of BBOT tags across aggregated occurrences.",
    )
    modules: PropertyRef = PropertyRef(
        "modules",
        description="Union of BBOT modules across aggregated occurrences.",
    )
    resolved_hosts: PropertyRef = PropertyRef(
        "resolved_hosts",
        description="Union of DNS names and IP addresses resolved by BBOT.",
    )
    discovery_contexts: PropertyRef = PropertyRef(
        "discovery_contexts",
        description="Union of BBOT discovery context strings.",
    )
    scope_distance: PropertyRef = PropertyRef(
        "scope_distance",
        description="Smallest BBOT scope distance among aggregated occurrences.",
    )
    web_spider_distance: PropertyRef = PropertyRef(
        "web_spider_distance",
        description="Smallest web spider distance among aggregated occurrences.",
    )
    observed_at: PropertyRef = PropertyRef(
        "observed_at",
        description="Timestamp of the latest aggregated occurrence.",
    )
    source_uri: PropertyRef = PropertyRef(
        "source_uri",
        description="Local path or object-store URI of the selected report.",
    )


@dataclass(frozen=True)
class BbotScanSchema(CartographyNodeSchema):
    """Represents the selected completed BBOT scan."""

    label: str = "BbotScan"
    scoped_cleanup: bool = False
    properties: BbotNodeProperties = BbotNodeProperties()


@dataclass(frozen=True)
class BbotDNSNameSchema(CartographyNodeSchema):
    """Represents a normalized DNS name observed by BBOT."""

    label: str = "BbotDNSName"
    scoped_cleanup: bool = False
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([DNS_RECORD])
    properties: BbotNodeProperties = BbotNodeProperties()


@dataclass(frozen=True)
class BbotIPAddressSchema(CartographyNodeSchema):
    """Represents a canonical IPv4 or IPv6 address observed by BBOT."""

    label: str = "BbotIPAddress"
    scoped_cleanup: bool = False
    properties: BbotNodeProperties = BbotNodeProperties()


@dataclass(frozen=True)
class BbotIPRangeSchema(CartographyNodeSchema):
    """Represents a canonical IP network observed by BBOT."""

    label: str = "BbotIPRange"
    scoped_cleanup: bool = False
    properties: BbotNodeProperties = BbotNodeProperties()


@dataclass(frozen=True)
class BbotOpenTCPPortSchema(CartographyNodeSchema):
    """Represents an open TCP endpoint observed by BBOT."""

    label: str = "BbotOpenTCPPort"
    scoped_cleanup: bool = False
    properties: BbotNodeProperties = BbotNodeProperties()


@dataclass(frozen=True)
class BbotURLSchema(CartographyNodeSchema):
    """Represents a canonical URL using BBOT's configured deduplication behavior."""

    label: str = "BbotURL"
    scoped_cleanup: bool = False
    properties: BbotNodeProperties = BbotNodeProperties()


@dataclass(frozen=True)
class BbotASNSchema(CartographyNodeSchema):
    """Represents an autonomous system observed by BBOT."""

    label: str = "BbotASN"
    scoped_cleanup: bool = False
    properties: BbotNodeProperties = BbotNodeProperties()


@dataclass(frozen=True)
class BbotTechnologySchema(CartographyNodeSchema):
    """Represents a technology detected on a host, effective port, or URL."""

    label: str = "BbotTechnology"
    scoped_cleanup: bool = False
    properties: BbotNodeProperties = BbotNodeProperties()


@dataclass(frozen=True)
class BbotEmailAddressSchema(CartographyNodeSchema):
    """Represents a normalized email address observed by BBOT."""

    label: str = "BbotEmailAddress"
    scoped_cleanup: bool = False
    properties: BbotNodeProperties = BbotNodeProperties()


@dataclass(frozen=True)
class BbotOrgStubSchema(CartographyNodeSchema):
    """Represents a normalized organization stub observed by BBOT."""

    label: str = "BbotOrgStub"
    scoped_cleanup: bool = False
    properties: BbotNodeProperties = BbotNodeProperties()


@dataclass(frozen=True)
class BbotSocialSchema(CartographyNodeSchema):
    """Represents a social profile observed by BBOT."""

    label: str = "BbotSocial"
    scoped_cleanup: bool = False
    properties: BbotNodeProperties = BbotNodeProperties()


@dataclass(frozen=True)
class BbotStorageBucketSchema(CartographyNodeSchema):
    """Represents an object storage bucket observed by BBOT."""

    label: str = "BbotStorageBucket"
    scoped_cleanup: bool = False
    properties: BbotNodeProperties = BbotNodeProperties()


@dataclass(frozen=True)
class BbotFindingSchema(CartographyNodeSchema):
    """Represents a security finding detected by BBOT."""

    label: str = "BbotFinding"
    scoped_cleanup: bool = False
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([SECURITY_ISSUE])
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


# Runtime MatchLinks can connect several concrete event types. This catalog keeps
# generated schema documentation aligned with the finite endpoint combinations.
BBOT_RELATIONSHIP_CATALOG: tuple[tuple[str, str, str, str], ...] = (
    *(
        (
            source_schema.label,
            "DISCOVERED_FROM",
            target_schema.label,
            "Connects a BBOT entity to the nearest supported parent ancestor that discovered it.",
        )
        for event_type, source_schema in BBOT_SCHEMAS.items()
        if event_type != "SCAN"
        for target_schema in BBOT_SCHEMAS.values()
    ),
    *(
        (
            schema.label,
            "OBSERVED_IN",
            "BbotScan",
            "Connects a BBOT entity to the completed scan that observed it.",
        )
        for event_type, schema in BBOT_SCHEMAS.items()
        if event_type != "SCAN"
    ),
    (
        "BbotDNSName",
        "RESOLVES_TO",
        "BbotDNSName",
        "Connects a DNS name to another DNS name returned by BBOT resolution.",
    ),
    (
        "BbotDNSName",
        "RESOLVES_TO",
        "BbotIPAddress",
        "Connects a DNS name to an IP address returned by BBOT resolution.",
    ),
    (
        "BbotDNSName",
        "HAS_OPEN_PORT",
        "BbotOpenTCPPort",
        "Connects a DNS name to an open TCP endpoint on that host.",
    ),
    (
        "BbotIPAddress",
        "HAS_OPEN_PORT",
        "BbotOpenTCPPort",
        "Connects an IP address to an open TCP endpoint on that host.",
    ),
    *(
        (
            "BbotURL",
            "HOSTED_BY",
            target_label,
            "Connects a URL to the endpoint or host that serves it.",
        )
        for target_label in (
            "BbotOpenTCPPort",
            "BbotDNSName",
            "BbotIPAddress",
        )
    ),
    *(
        (
            "BbotTechnology",
            "DETECTED_ON",
            target_label,
            "Connects a detected technology to the URL, endpoint, or host where BBOT found it.",
        )
        for target_label in (
            "BbotURL",
            "BbotOpenTCPPort",
            "BbotDNSName",
            "BbotIPAddress",
        )
    ),
    *(
        (
            "BbotFinding",
            "AFFECTS",
            target_label,
            "Connects a BBOT finding to the asset it affects.",
        )
        for target_label in (
            "BbotURL",
            "BbotOpenTCPPort",
            "BbotStorageBucket",
            "BbotDNSName",
            "BbotIPAddress",
        )
    ),
    (
        "BbotIPAddress",
        "ANNOUNCED_BY",
        "BbotASN",
        "Connects an IP address to the autonomous system that announces it.",
    ),
)


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
    """Connects two BBOT entities observed in the selected scan."""

    __cartography_introspection_exclude__ = True

    source_node_label: str = "BbotDNSName"
    target_node_label: str = "BbotScan"
    rel_label: str = "OBSERVED_IN"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("source_id")},
    )
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("target_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    properties: BbotMatchLinkProperties = BbotMatchLinkProperties()


@dataclass(frozen=True)
class BbotCleanupObservedInRel(CartographyRelSchema):
    """Cleanup-only relationship that enables GraphJob node cleanup."""

    __cartography_introspection_exclude__ = True

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

    __cartography_introspection_exclude__ = True

    label: str = "BbotScan"
    scoped_cleanup: bool = False
    properties: BbotNodeProperties = BbotNodeProperties()
    other_relationships: OtherRelationships = OtherRelationships(
        [BbotCleanupObservedInRel()],
    )
