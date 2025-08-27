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
class ADUserNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    samaccountname: PropertyRef = PropertyRef("samaccountname", extra_index=True)
    userprincipalname: PropertyRef = PropertyRef("userprincipalname", extra_index=True)
    distinguishedname: PropertyRef = PropertyRef("distinguishedname", extra_index=True)
    objectsid: PropertyRef = PropertyRef("objectsid", extra_index=True)
    enabled: PropertyRef = PropertyRef("enabled")
    pwdlastset: PropertyRef = PropertyRef("pwdlastset")
    lastlogontimestamp: PropertyRef = PropertyRef("lastlogontimestamp")
    spns: PropertyRef = PropertyRef("spns")
    ou_dn: PropertyRef = PropertyRef("ou_dn")
    memberof_dns: PropertyRef = PropertyRef("memberof_dns")


@dataclass(frozen=True)
class UserToDomainRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class UserToDomainRel(CartographyRelSchema):
    target_node_label: str = "ADDomain"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("DOMAIN_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: UserToDomainRelProperties = UserToDomainRelProperties()


@dataclass(frozen=True)
class UserToOURelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class UserToOURel(CartographyRelSchema):
    target_node_label: str = "ADOrganizationalUnit"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"distinguishedname": PropertyRef("ou_dn")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "IN_OU"
    properties: UserToOURelProperties = UserToOURelProperties()


@dataclass(frozen=True)
class UserToGroupRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class UserToGroupRel(CartographyRelSchema):
    target_node_label: str = "ADGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"distinguishedname": PropertyRef("memberof_dns", one_to_many=True)}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF"
    properties: UserToGroupRelProperties = UserToGroupRelProperties()


@dataclass(frozen=True)
class ADUserSchema(CartographyNodeSchema):
    label: str = "ADUser"
    properties: ADUserNodeProperties = ADUserNodeProperties()
    sub_resource_relationship: UserToDomainRel = UserToDomainRel()
    other_relationships: OtherRelationships = OtherRelationships([UserToOURel(), UserToGroupRel()])

