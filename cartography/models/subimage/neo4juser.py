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
class SubImageNeo4jUserNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("username")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SubImageNeo4jUserToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SubImageTenant)-[:RESOURCE]->(:SubImageNeo4jUser)
class SubImageNeo4jUserToTenantRel(CartographyRelSchema):
    target_node_label: str = "SubImageTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TENANT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SubImageNeo4jUserToTenantRelProperties = (
        SubImageNeo4jUserToTenantRelProperties()
    )


@dataclass(frozen=True)
class SubImageNeo4jUserSchema(CartographyNodeSchema):
    label: str = "SubImageNeo4jUser"
    properties: SubImageNeo4jUserNodeProperties = SubImageNeo4jUserNodeProperties()
    sub_resource_relationship: SubImageNeo4jUserToTenantRel = (
        SubImageNeo4jUserToTenantRel()
    )
