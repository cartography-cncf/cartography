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
class ADOrganizationalUnitNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    distinguishedname: PropertyRef = PropertyRef("distinguishedname", extra_index=True)
    name: PropertyRef = PropertyRef("name")
    parent_dn: PropertyRef = PropertyRef("parent_dn")
    gpo_ids: PropertyRef = PropertyRef("gpo_ids")


@dataclass(frozen=True)
class OUTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class OUToDomainRel(CartographyRelSchema):
    target_node_label: str = "ADDomain"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("DOMAIN_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: OUTenantRelProperties = OUTenantRelProperties()


@dataclass(frozen=True)
class OUToOURelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class OUToOURel(CartographyRelSchema):
    target_node_label: str = "ADOrganizationalUnit"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"distinguishedname": PropertyRef("parent_dn")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "PARENT_OU"
    properties: OUToOURelProperties = OUToOURelProperties()


@dataclass(frozen=True)
class OUToGPORelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class OUToGPORel(CartographyRelSchema):
    target_node_label: str = "ADGPO"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("gpo_ids", one_to_many=True)}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_GPO"
    properties: OUToGPORelProperties = OUToGPORelProperties()


@dataclass(frozen=True)
class ADOrganizationalUnitSchema(CartographyNodeSchema):
    label: str = "ADOrganizationalUnit"
    properties: ADOrganizationalUnitNodeProperties = ADOrganizationalUnitNodeProperties()
    sub_resource_relationship: OUToDomainRel = OUToDomainRel()
    other_relationships: OtherRelationships = OtherRelationships([OUToOURel(), OUToGPORel()])

