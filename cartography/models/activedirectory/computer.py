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
class ADComputerNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    samaccountname: PropertyRef = PropertyRef("samaccountname")
    dns_host_name: PropertyRef = PropertyRef("dns_host_name")
    distinguishedname: PropertyRef = PropertyRef("distinguishedname", extra_index=True)
    objectsid: PropertyRef = PropertyRef("objectsid", extra_index=True)
    is_domain_controller: PropertyRef = PropertyRef("is_domain_controller")
    operatingsystem: PropertyRef = PropertyRef("operatingsystem")
    lastlogontimestamp: PropertyRef = PropertyRef("lastlogontimestamp")
    spns: PropertyRef = PropertyRef("spns")
    ou_dn: PropertyRef = PropertyRef("ou_dn")
    memberof_dns: PropertyRef = PropertyRef("memberof_dns")
    site_name: PropertyRef = PropertyRef("site_name")


@dataclass(frozen=True)
class ComputerToDomainRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ComputerToDomainRel(CartographyRelSchema):
    target_node_label: str = "ADDomain"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("DOMAIN_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ComputerToDomainRelProperties = ComputerToDomainRelProperties()


@dataclass(frozen=True)
class ComputerToOURelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ComputerToOURel(CartographyRelSchema):
    target_node_label: str = "ADOrganizationalUnit"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"distinguishedname": PropertyRef("ou_dn")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "IN_OU"
    properties: ComputerToOURelProperties = ComputerToOURelProperties()


@dataclass(frozen=True)
class ComputerToGroupRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ComputerToGroupRel(CartographyRelSchema):
    target_node_label: str = "ADGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"distinguishedname": PropertyRef("memberof_dns", one_to_many=True)}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF"
    properties: ComputerToGroupRelProperties = ComputerToGroupRelProperties()


@dataclass(frozen=True)
class ComputerToSiteRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ComputerToSiteRel(CartographyRelSchema):
    target_node_label: str = "ADSite"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("site_name")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "IN_SITE"
    properties: ComputerToSiteRelProperties = ComputerToSiteRelProperties()


@dataclass(frozen=True)
class ADComputerSchema(CartographyNodeSchema):
    label: str = "ADComputer"
    properties: ADComputerNodeProperties = ADComputerNodeProperties()
    sub_resource_relationship: ComputerToDomainRel = ComputerToDomainRel()
    other_relationships: OtherRelationships = OtherRelationships([ComputerToOURel(), ComputerToGroupRel(), ComputerToSiteRel()])

