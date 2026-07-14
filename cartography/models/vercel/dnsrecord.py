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
class VercelDNSRecordNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="DNS record ID.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Timestamp of the last update."
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="DNS record name."
    )
    type: PropertyRef = PropertyRef("type", description="DNS record type.")
    value: PropertyRef = PropertyRef("value", description="DNS record value.")
    ttl: PropertyRef = PropertyRef("ttl", description="DNS record time to live.")
    priority: PropertyRef = PropertyRef(
        "priority", description="DNS record priority when applicable."
    )
    created_at: PropertyRef = PropertyRef(
        "createdAt", description="Timestamp when the DNS record was created."
    )


@dataclass(frozen=True)
class VercelDNSRecordToTeamRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:VercelTeam)-[:RESOURCE]->(:VercelDNSRecord)
class VercelDNSRecordToTeamRel(CartographyRelSchema):
    """The Vercel team contains this DNS record as a resource."""

    target_node_label: str = "VercelTeam"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TEAM_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: VercelDNSRecordToTeamRelProperties = (
        VercelDNSRecordToTeamRelProperties()
    )


@dataclass(frozen=True)
class VercelDNSRecordToDomainRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:VercelDomain)-[:HAS_DNS_RECORD]->(:VercelDNSRecord)
class VercelDNSRecordToDomainRel(CartographyRelSchema):
    """The Vercel domain contains this DNS record."""

    target_node_label: str = "VercelDomain"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("domain_name", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_DNS_RECORD"
    properties: VercelDNSRecordToDomainRelProperties = (
        VercelDNSRecordToDomainRelProperties()
    )


@dataclass(frozen=True)
class VercelDNSRecordSchema(CartographyNodeSchema):
    """A Vercel DNS record with the canonical DNSRecord label."""

    label: str = "VercelDNSRecord"
    properties: VercelDNSRecordNodeProperties = VercelDNSRecordNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["DNSRecord"])
    sub_resource_relationship: VercelDNSRecordToTeamRel = VercelDNSRecordToTeamRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [VercelDNSRecordToDomainRel()],
    )
