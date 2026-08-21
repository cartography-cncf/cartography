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
class RenderRouteNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="ID of the Render redirect/rewrite rule."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    owner_id: PropertyRef = PropertyRef(
        "ownerId", description="ID of the owning Render workspace."
    )
    service_id: PropertyRef = PropertyRef(
        "serviceId",
        extra_index=True,
        description="ID of the service this rule applies to.",
    )
    type: PropertyRef = PropertyRef("type", description="`redirect` or `rewrite`.")
    source: PropertyRef = PropertyRef("source", description="Source path pattern.")
    destination: PropertyRef = PropertyRef(
        "destination", description="Target path or URL."
    )
    priority: PropertyRef = PropertyRef(
        "priority", description="Order this rule is applied in, starting at 0."
    )


@dataclass(frozen=True)
class RenderRouteToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:RenderTenant)-[:RESOURCE]->(:RenderRoute)
class RenderRouteToTenantRel(CartographyRelSchema):
    """Connects a Render workspace to a redirect/rewrite rule that it contains."""

    target_node_label: str = "RenderTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("OWNER_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: RenderRouteToTenantRelProperties = RenderRouteToTenantRelProperties()


@dataclass(frozen=True)
class RenderRouteToServiceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:RenderService)-[:HAS_ROUTE]->(:RenderRoute)
class RenderRouteToServiceRel(CartographyRelSchema):
    """Connects a Render service to a redirect/rewrite rule configured on it."""

    target_node_label: str = "RenderService"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("serviceId")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_ROUTE"
    properties: RenderRouteToServiceRelProperties = RenderRouteToServiceRelProperties()


@dataclass(frozen=True)
class RenderRouteSchema(CartographyNodeSchema):
    """A redirect or rewrite rule configured on a Render service."""

    label: str = "RenderRoute"
    properties: RenderRouteNodeProperties = RenderRouteNodeProperties()
    sub_resource_relationship: RenderRouteToTenantRel = RenderRouteToTenantRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [RenderRouteToServiceRel()],
    )
