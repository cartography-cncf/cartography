from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties, CartographyNodeSchema
from cartography.models.core.relationships import (
    CartographyRelProperties,
    CartographyRelSchema,
    LinkDirection,
    make_target_node_matcher,
    TargetNodeMatcher,
)


@dataclass(frozen=True)
class ADDomainNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    dns_name: PropertyRef = PropertyRef("dns_name", extra_index=True)
    netbios_name: PropertyRef = PropertyRef("netbios_name", extra_index=True)
    sid: PropertyRef = PropertyRef("sid", extra_index=True)


@dataclass(frozen=True)
class DomainToForestRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DomainToForestRel(CartographyRelSchema):
    target_node_label: str = "ADForest"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("FOREST_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_DOMAIN"
    properties: DomainToForestRelProperties = DomainToForestRelProperties()


@dataclass(frozen=True)
class ADDomainSchema(CartographyNodeSchema):
    label: str = "ADDomain"
    properties: ADDomainNodeProperties = ADDomainNodeProperties()
    sub_resource_relationship: DomainToForestRel = DomainToForestRel()

