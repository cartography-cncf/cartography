from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties, CartographyNodeSchema
from cartography.models.core.relationships import (
    CartographyRelProperties,
    CartographyRelSchema,
    LinkDirection,
    make_target_node_matcher,
    TargetNodeMatcher,
    OtherRelationships,
)


@dataclass(frozen=True)
class ADSiteNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SiteToForestRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SiteToForestRel(CartographyRelSchema):
    target_node_label: str = "ADForest"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("FOREST_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SiteToForestRelProperties = SiteToForestRelProperties()


@dataclass(frozen=True)
class SiteToSubnetRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SiteToSubnetRel(CartographyRelSchema):
    target_node_label: str = "ADSubnet"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("subnet_ids", one_to_many=True)}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_SUBNET"
    properties: SiteToSubnetRelProperties = SiteToSubnetRelProperties()


@dataclass(frozen=True)
class SiteReplicatesWithRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SiteReplicatesWithRel(CartographyRelSchema):
    target_node_label: str = "ADSite"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("replicate_site_names", one_to_many=True)}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "REPLICATES_WITH"
    properties: SiteReplicatesWithRelProperties = SiteReplicatesWithRelProperties()


@dataclass(frozen=True)
class ADSiteSchema(CartographyNodeSchema):
    label: str = "ADSite"
    properties: ADSiteNodeProperties = ADSiteNodeProperties()
    sub_resource_relationship: SiteToForestRel = SiteToForestRel()
    other_relationships: OtherRelationships = OtherRelationships([SiteToSubnetRel(), SiteReplicatesWithRel()])

