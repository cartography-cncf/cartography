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
class ADGroupNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    samaccountname: PropertyRef = PropertyRef("samaccountname", extra_index=True)
    distinguishedname: PropertyRef = PropertyRef("distinguishedname", extra_index=True)
    objectsid: PropertyRef = PropertyRef("objectsid", extra_index=True)
    scope: PropertyRef = PropertyRef("scope")
    type: PropertyRef = PropertyRef("type")
    is_builtin: PropertyRef = PropertyRef("is_builtin")
    member_dns: PropertyRef = PropertyRef("member_dns")
    memberof_dns: PropertyRef = PropertyRef("memberof_dns")


@dataclass(frozen=True)
class GroupToDomainRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GroupToDomainRel(CartographyRelSchema):
    target_node_label: str = "ADDomain"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("DOMAIN_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GroupToDomainRelProperties = GroupToDomainRelProperties()


@dataclass(frozen=True)
class GroupToGroupRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GroupToGroupRel(CartographyRelSchema):
    target_node_label: str = "ADGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"distinguishedname": PropertyRef("memberof_dns", one_to_many=True)}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF"
    properties: GroupToGroupRelProperties = GroupToGroupRelProperties()


@dataclass(frozen=True)
class GroupToUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GroupToUserRel(CartographyRelSchema):
    target_node_label: str = "ADUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"distinguishedname": PropertyRef("member_dns", one_to_many=True)}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_MEMBER_USER"
    properties: GroupToUserRelProperties = GroupToUserRelProperties()


@dataclass(frozen=True)
class GroupToComputerRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GroupToComputerRel(CartographyRelSchema):
    target_node_label: str = "ADComputer"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"distinguishedname": PropertyRef("member_dns", one_to_many=True)}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_MEMBER_COMPUTER"
    properties: GroupToComputerRelProperties = GroupToComputerRelProperties()


@dataclass(frozen=True)
class ADGroupSchema(CartographyNodeSchema):
    label: str = "ADGroup"
    properties: ADGroupNodeProperties = ADGroupNodeProperties()
    sub_resource_relationship: GroupToDomainRel = GroupToDomainRel()
    other_relationships: OtherRelationships = OtherRelationships([GroupToGroupRel(), GroupToUserRel(), GroupToComputerRel()])

