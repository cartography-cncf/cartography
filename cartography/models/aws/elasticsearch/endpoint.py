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
from cartography.models.ontology.labels import DNS_RECORD


@dataclass(frozen=True)
class ESDomainEndpointIpNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="The IP address.")
    ip: PropertyRef = PropertyRef("ip", description="The IP address.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ESDomainEndpointIpSchema(CartographyNodeSchema):
    """An IP address that an Elasticsearch domain endpoint resolves to."""

    # The same address can be resolved from endpoints in many accounts, so it has no owning
    # account and the Elasticsearch sync never deletes it.

    label: str = "Ip"
    properties: ESDomainEndpointIpNodeProperties = ESDomainEndpointIpNodeProperties()


@dataclass(frozen=True)
class ESDomainEndpointDNSRecordNodeProperties(CartographyNodeProperties):
    # The descriptions live on AWSDNSRecordSchema, which documents the shared label.
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name", extra_index=True)
    name_normalized: PropertyRef = PropertyRef("name_normalized")
    type: PropertyRef = PropertyRef("type")
    value: PropertyRef = PropertyRef("value")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ESDomainEndpointDNSRecordToESDomainRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AWSDNSRecord)-[:DNS_POINTS_TO]->(:AWSESDomain)
class ESDomainEndpointDNSRecordToESDomainRel(CartographyRelSchema):
    """The record resolves to the domain's endpoint."""

    target_node_label: str = "AWSESDomain"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("domain_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "DNS_POINTS_TO"
    properties: ESDomainEndpointDNSRecordToESDomainRelProperties = (
        ESDomainEndpointDNSRecordToESDomainRelProperties()
    )


@dataclass(frozen=True)
class ESDomainEndpointDNSRecordToIpRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AWSDNSRecord)-[:DNS_POINTS_TO]->(:Ip)
class ESDomainEndpointDNSRecordToIpRel(CartographyRelSchema):
    """The record resolves to the IP address."""

    target_node_label: str = "Ip"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ip_addresses", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "DNS_POINTS_TO"
    properties: ESDomainEndpointDNSRecordToIpRelProperties = (
        ESDomainEndpointDNSRecordToIpRelProperties()
    )


@dataclass(frozen=True)
class ESDomainEndpointDNSRecordSchema(CartographyNodeSchema):
    """An `A` record that Cartography resolves from an Elasticsearch domain endpoint."""

    # These records share the AWSDNSRecord label with Route53 records, so they have no
    # RESOURCE edge from the account: an account-scoped cleanup of the shared label would let
    # the Route53 and Elasticsearch syncs delete each other's records. The Elasticsearch sync
    # cleans them up through their domain instead.

    label: str = "AWSDNSRecord"
    properties: ESDomainEndpointDNSRecordNodeProperties = (
        ESDomainEndpointDNSRecordNodeProperties()
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([DNS_RECORD])
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ESDomainEndpointDNSRecordToESDomainRel(),
            ESDomainEndpointDNSRecordToIpRel(),
        ],
    )
