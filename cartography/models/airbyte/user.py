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
class AirbyteUserNodeProperties(CartographyNodeProperties):
    name: PropertyRef = PropertyRef('name')
    email: PropertyRef = PropertyRef('email')
    id: PropertyRef = PropertyRef('id')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class AirbyteUserToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AirbyteOrganization)-[:RESOURCE]->(:AirbyteUser)
class AirbyteUserToOrganizationRel(CartographyRelSchema):
    target_node_label: str = "AirbyteOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AirbyteUserToOrganizationRelProperties = (
        AirbyteUserToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class AirbyteUserSchema(CartographyNodeSchema):
    label: str = 'AirbyteUser'
    properties: AirbyteUserNodeProperties = AirbyteUserNodeProperties()
    sub_resource_relationship: AirbyteUserToOrganizationRel = AirbyteUserToOrganizationRel()
