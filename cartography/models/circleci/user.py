from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class CircleCIUserNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    login: PropertyRef = PropertyRef("login", extra_index=True)
    name: PropertyRef = PropertyRef("name")
    avatar_url: PropertyRef = PropertyRef("avatar_url")


@dataclass(frozen=True)
class CircleCIUserToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:CircleCIOrganization)-[:RESOURCE]->(:CircleCIUser)
class CircleCIUserToOrganizationRel(CartographyRelSchema):
    target_node_label: str = "CircleCIOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: CircleCIUserToOrganizationRelProperties = (
        CircleCIUserToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class CircleCIUserSchema(CartographyNodeSchema):
    label: str = "CircleCIUser"
    properties: CircleCIUserNodeProperties = CircleCIUserNodeProperties()
    sub_resource_relationship: CircleCIUserToOrganizationRel = (
        CircleCIUserToOrganizationRel()
    )
