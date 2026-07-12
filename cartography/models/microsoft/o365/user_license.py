from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_source_node_matcher
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import MatchLinkSubResource
from cartography.models.core.relationships import SourceNodeMatcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class EntraUserToM365LicenseRelProperties(CartographyRelProperties):
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
# (:EntraUser)-[:ASSIGNED_LICENSE]->(:M365License)
class EntraUserToM365LicenseRel(CartographyRelSchema):
    target_node_label: str = "M365License"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"sku_id": PropertyRef("sku_id")},
    )
    target_node_sub_resource: MatchLinkSubResource = MatchLinkSubResource(
        target_node_label="EntraTenant",
        target_node_matcher=make_target_node_matcher(
            {"id": PropertyRef("_sub_resource_id", set_in_kwargs=True)},
        ),
        direction=LinkDirection.INWARD,
        rel_label="RESOURCE",
    )
    source_node_label: str = "EntraUser"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("user_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ASSIGNED_LICENSE"
    properties: EntraUserToM365LicenseRelProperties = (
        EntraUserToM365LicenseRelProperties()
    )
