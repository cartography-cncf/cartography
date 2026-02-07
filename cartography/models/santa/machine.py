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
class SantaMachineNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    hostname: PropertyRef = PropertyRef("hostname", extra_index=True)
    serial_number: PropertyRef = PropertyRef("serial_number", extra_index=True)
    platform: PropertyRef = PropertyRef("platform")
    model: PropertyRef = PropertyRef("model")
    os_version: PropertyRef = PropertyRef("os_version")
    source_name: PropertyRef = PropertyRef("source_name")
    last_seen: PropertyRef = PropertyRef("last_seen")


@dataclass(frozen=True)
class SantaMachineToSantaUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SantaMachine)-[:PRIMARY_USER]->(:SantaUser)
class SantaMachineToSantaUserRel(CartographyRelSchema):
    target_node_label: str = "SantaUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("primary_user_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "PRIMARY_USER"
    properties: SantaMachineToSantaUserRelProperties = (
        SantaMachineToSantaUserRelProperties()
    )


@dataclass(frozen=True)
class SantaMachineSchema(CartographyNodeSchema):
    label: str = "SantaMachine"
    scoped_cleanup: bool = False
    properties: SantaMachineNodeProperties = SantaMachineNodeProperties()
    other_relationships: OtherRelationships = OtherRelationships(
        rels=[SantaMachineToSantaUserRel()],
    )
