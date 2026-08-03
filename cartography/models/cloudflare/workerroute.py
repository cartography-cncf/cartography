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
class CloudflareWorkerRouteNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Route ID.")
    pattern: PropertyRef = PropertyRef(
        "pattern",
        extra_index=True,
        description="URL pattern incoming requests are matched against.",
    )
    script: PropertyRef = PropertyRef(
        "script",
        description="Name of the Worker script invoked when the route matches.",
    )
    zone_id: PropertyRef = PropertyRef(
        "zone_id",
        set_in_kwargs=True,
        description="ID of the zone the route is defined in.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class CloudflareWorkerRouteToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:CloudflareWorkerRoute)<-[:RESOURCE]-(:CloudflareAccount)
class CloudflareWorkerRouteToAccountRel(CartographyRelSchema):
    """The account contains the Worker route."""

    target_node_label: str = "CloudflareAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("account_id", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: CloudflareWorkerRouteToAccountRelProperties = (
        CloudflareWorkerRouteToAccountRelProperties()
    )


@dataclass(frozen=True)
class CloudflareWorkerRouteToZoneRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:CloudflareZone)-[:HAS_ROUTE]->(:CloudflareWorkerRoute)
class CloudflareWorkerRouteToZoneRel(CartographyRelSchema):
    """The DNS zone routes matching requests through the Worker route."""

    target_node_label: str = "CloudflareZone"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("zone_id", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_ROUTE"
    properties: CloudflareWorkerRouteToZoneRelProperties = (
        CloudflareWorkerRouteToZoneRelProperties()
    )


@dataclass(frozen=True)
class CloudflareWorkerRouteToScriptRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:CloudflareWorkerRoute)-[:ROUTES_TO]->(:CloudflareWorkerScript)
class CloudflareWorkerRouteToScriptRel(CartographyRelSchema):
    """The route invokes the Worker script."""

    target_node_label: str = "CloudflareWorkerScript"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("script_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ROUTES_TO"
    properties: CloudflareWorkerRouteToScriptRelProperties = (
        CloudflareWorkerRouteToScriptRelProperties()
    )


@dataclass(frozen=True)
class CloudflareWorkerRouteSchema(CartographyNodeSchema):
    """A route binding a zone URL pattern to a Cloudflare Worker script."""

    label: str = "CloudflareWorkerRoute"
    properties: CloudflareWorkerRouteNodeProperties = (
        CloudflareWorkerRouteNodeProperties()
    )
    sub_resource_relationship: CloudflareWorkerRouteToAccountRel = (
        CloudflareWorkerRouteToAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            CloudflareWorkerRouteToZoneRel(),
            CloudflareWorkerRouteToScriptRel(),
        ],
    )
