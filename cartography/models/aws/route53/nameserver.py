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
class NameServerNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("id", extra_index=True)
    zoneid: PropertyRef = PropertyRef("zoneid")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class NameServerToZoneRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class NameServerToZoneRel(CartographyRelSchema):
    target_node_label: str = "AWSDNSZone"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"zoneid": PropertyRef("zoneid")}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "NAMESERVER"
    properties: NameServerToZoneRelProperties = NameServerToZoneRelProperties()


@dataclass(frozen=True)
class NameServerToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class NameServerToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: NameServerToAWSAccountRelProperties = (
        NameServerToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class NameServerSchema(CartographyNodeSchema):
    label: str = "NameServer"
    properties: NameServerNodeProperties = NameServerNodeProperties()
    sub_resource_relationship: NameServerToAWSAccountRel = NameServerToAWSAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [NameServerToZoneRel()]
    )
