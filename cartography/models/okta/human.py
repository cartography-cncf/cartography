# DEPRECATED
# The usage of Human at module level is deprecated. This will be removed in a future release.
# Refer to https://github.com/cartography-cncf/cartography/discussions/1579
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
class HumanProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class HumanToUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:OktaUser)<-[:IDENTITY_OKTA]-(:Human)
class HumanToUserRel(CartographyRelSchema):
    target_node_label: str = "OktaUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"email": PropertyRef("email", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: HumanToUserRelProperties = HumanToUserRelProperties()


@dataclass(frozen=True)
class HumanSchema(CartographyNodeSchema):
    label: str = "Human"
    properties: HumanProperties = HumanProperties()
    other_relationships: OtherRelationships = OtherRelationships([HumanToUserRel()])
