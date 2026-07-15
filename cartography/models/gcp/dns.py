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


@dataclass(frozen=True)
class GCPDNSZoneNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", extra_index=True, description="Stable identifier for this resource."
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="The name of the zone."
    )
    dns_name: PropertyRef = PropertyRef(
        "dns_name",
        description='The DNS name of this managed zone, for instance "example.com.".',
    )
    description: PropertyRef = PropertyRef(
        "description", description="An optional description of the zone."
    )
    visibility: PropertyRef = PropertyRef(
        "visibility",
        description="The zone's visibility: `public` zones are exposed to the Internet, while `private` zones are visible only to Virtual Private Cloud resources.",
    )
    dnssec_state: PropertyRef = PropertyRef(
        "dnssec_state",
        description="DNSSEC state for the managed zone, e.g. `on` or `off`.",
    )
    dnssec_key_signing_algorithm: PropertyRef = PropertyRef(
        "dnssec_key_signing_algorithm",
        description="Algorithm configured for the DNSSEC key-signing key, when present.",
    )
    dnssec_zone_signing_algorithm: PropertyRef = PropertyRef(
        "dnssec_zone_signing_algorithm",
        description="Algorithm configured for the DNSSEC zone-signing key, when present.",
    )
    kind: PropertyRef = PropertyRef(
        "kind", description="Google DNS API resource kind identifier."
    )
    nameservers: PropertyRef = PropertyRef(
        "nameservers", description="Virtual name servers the zone is delegated to."
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="The date and time the zone was created."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
class GCPDNSZoneToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
# (:GCPProject)-[:RESOURCE]->(:GCPDNSZone)
class GCPDNSZoneToProjectRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPDNSZoneToProjectRelProperties = GCPDNSZoneToProjectRelProperties()


@dataclass(frozen=True)
class GCPDNSZoneSchema(CartographyNodeSchema):
    """Representation of a GCP [DNS Zone](https://cloud.google.com/dns/docs/reference/v1/)."""

    label: str = "GCPDNSZone"
    properties: GCPDNSZoneNodeProperties = GCPDNSZoneNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["DNSZone"])
    sub_resource_relationship: GCPDNSZoneToProjectRel = GCPDNSZoneToProjectRel()


@dataclass(frozen=True)
class GCPRecordSetNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", extra_index=True, description="Stable identifier for this resource."
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="The name of the Resource Record Set."
    )
    type: PropertyRef = PropertyRef(
        "type",
        description="The identifier of a supported record type. See the list of [Supported DNS record types](https://cloud.google.om/dns/docs/overview#supported_dns_record_types).",
    )
    ttl: PropertyRef = PropertyRef(
        "ttl",
        description="Number of seconds that this ResourceRecordSet can be cached by resolvers.",
    )
    data: PropertyRef = PropertyRef("data", description="Data contained in the record.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
class GCPRecordSetToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
# (:GCPProject)-[:RESOURCE]->(:GCPRecordSet)
class GCPRecordSetToProjectRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPRecordSetToProjectRelProperties = (
        GCPRecordSetToProjectRelProperties()
    )


@dataclass(frozen=True)
class GCPRecordSetToZoneRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
# (:GCPDNSZone)-[:HAS_RECORD]->(:GCPRecordSet)
class GCPRecordSetToZoneRel(CartographyRelSchema):
    target_node_label: str = "GCPDNSZone"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("zone_id")}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_RECORD"
    properties: GCPRecordSetToZoneRelProperties = GCPRecordSetToZoneRelProperties()


@dataclass(frozen=True)
class GCPRecordSetSchema(CartographyNodeSchema):
    """Representation of a GCP [Resource Record Set](https://cloud.google.com/dns/docs/reference/v1/)."""

    label: str = "GCPRecordSet"
    properties: GCPRecordSetNodeProperties = GCPRecordSetNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["DNSRecord"])
    sub_resource_relationship: GCPRecordSetToProjectRel = GCPRecordSetToProjectRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GCPRecordSetToZoneRel(),
        ]
    )
