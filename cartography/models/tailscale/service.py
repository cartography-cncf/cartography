from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class TailscaleServiceNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Service ID in grant selector format (eg. `svc:web-server`)."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )
    name: PropertyRef = PropertyRef(
        "name", description="The unique name of the service."
    )
    comment: PropertyRef = PropertyRef(
        "comment", description="An optional description for the service."
    )
    ipv4_address: PropertyRef = PropertyRef(
        "ipv4_address", description="The IPv4 address assigned to the service."
    )
    ipv6_address: PropertyRef = PropertyRef(
        "ipv6_address", description="The IPv6 address assigned to the service."
    )
    ports: PropertyRef = PropertyRef(
        "ports", description='Native list of protocol:port pairs (eg. `["tcp:443"]`).'
    )
    tags: PropertyRef = PropertyRef(
        "tags", description="JSON-serialized list of tags associated with the service."
    )


@dataclass(frozen=True)
class TailscaleServiceToTailnetRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last Cartography update.",
    )


@dataclass(frozen=True)
# (:TailscaleTailnet)-[:RESOURCE]->(:TailscaleService)
class TailscaleServiceToTailnetRel(CartographyRelSchema):
    """Defines the RESOURCE relationship to TailscaleTailnet nodes."""

    target_node_label: str = "TailscaleTailnet"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("org", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: TailscaleServiceToTailnetRelProperties = (
        TailscaleServiceToTailnetRelProperties()
    )


@dataclass(frozen=True)
class TailscaleServiceToTagRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last Cartography update.",
    )


@dataclass(frozen=True)
# (:TailscaleService)-[:TAGGED]->(:TailscaleTag)
class TailscaleServiceToTagRel(CartographyRelSchema):
    """Defines the TAGGED relationship to TailscaleTag nodes."""

    target_node_label: str = "TailscaleTag"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("tag_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "TAGGED"
    properties: TailscaleServiceToTagRelProperties = (
        TailscaleServiceToTagRelProperties()
    )


@dataclass(frozen=True)
class TailscaleServiceSchema(CartographyNodeSchema):
    """
    A Tailscale Service published in the tailnet. Services are named resources backed by
    one or more device hosts, accessible via stable MagicDNS names.
    """

    label: str = "TailscaleService"
    properties: TailscaleServiceNodeProperties = TailscaleServiceNodeProperties()
    sub_resource_relationship: TailscaleServiceToTailnetRel = (
        TailscaleServiceToTailnetRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            TailscaleServiceToTagRel(),
        ],
    )
