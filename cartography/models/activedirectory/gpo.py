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
class ADGPONodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    displayname: PropertyRef = PropertyRef("displayname")
    version: PropertyRef = PropertyRef("version")
    wmifilter: PropertyRef = PropertyRef("wmifilter")


@dataclass(frozen=True)
class GPOToDomainRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GPOToDomainRel(CartographyRelSchema):
    target_node_label: str = "ADDomain"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("DOMAIN_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GPOToDomainRelProperties = GPOToDomainRelProperties()


@dataclass(frozen=True)
class ADGPOSchema(CartographyNodeSchema):
    label: str = "ADGPO"
    properties: ADGPONodeProperties = ADGPONodeProperties()
    sub_resource_relationship: GPOToDomainRel = GPOToDomainRel()

