from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_source_node_matcher
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import SourceNodeMatcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class AWSDNSZoneSubzoneRelProperties(CartographyRelProperties):
    # Mandatory fields for MatchLinks
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)


# MatchLink for creating SUBZONE relationships between DNS zones
@dataclass(frozen=True)
class AWSDNSZoneSubzoneMatchLink(CartographyRelSchema):
    target_node_label: str = "AWSDNSZone"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "zoneid": PropertyRef("subzone_id"),
        }
    )
    source_node_label: str = "AWSDNSZone"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {
            "zoneid": PropertyRef("zone_id"),
        }
    )
    properties: AWSDNSZoneSubzoneRelProperties = AWSDNSZoneSubzoneRelProperties()
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "SUBZONE"
