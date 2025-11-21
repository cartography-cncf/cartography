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
class KonnectRouteNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef('id')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)
    name: PropertyRef = PropertyRef('name')
    protocols: PropertyRef = PropertyRef('protocols')
    methods: PropertyRef = PropertyRef('methods')
    hosts: PropertyRef = PropertyRef('hosts')
    paths: PropertyRef = PropertyRef('paths')
    headers: PropertyRef = PropertyRef('headers')
    https_redirect_status_code: PropertyRef = PropertyRef('https_redirect_status_code')
    regex_priority: PropertyRef = PropertyRef('regex_priority')
    strip_path: PropertyRef = PropertyRef('strip_path')
    preserve_host: PropertyRef = PropertyRef('preserve_host')
    request_buffering: PropertyRef = PropertyRef('request_buffering')
    response_buffering: PropertyRef = PropertyRef('response_buffering')
    snis: PropertyRef = PropertyRef('snis')
    sources: PropertyRef = PropertyRef('sources')
    destinations: PropertyRef = PropertyRef('destinations')
    tags: PropertyRef = PropertyRef('tags')
    created_at: PropertyRef = PropertyRef('created_at')
    updated_at: PropertyRef = PropertyRef('updated_at')


@dataclass(frozen=True)
class KonnectRouteToControlPlaneRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class KonnectRouteToControlPlaneRel(CartographyRelSchema):
    target_node_label: str = 'KonnectControlPlane'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('CONTROL_PLANE_ID', set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RESOURCE"
    properties: KonnectRouteToControlPlaneRelProperties = KonnectRouteToControlPlaneRelProperties()


@dataclass(frozen=True)
class KonnectRouteToServiceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class KonnectRouteToServiceRel(CartographyRelSchema):
    target_node_label: str = 'KonnectService'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('SERVICE_ID', set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ROUTES_TO"
    properties: KonnectRouteToServiceRelProperties = KonnectRouteToServiceRelProperties()


@dataclass(frozen=True)
class KonnectRouteSchema(CartographyNodeSchema):
    label: str = 'KonnectRoute'
    properties: KonnectRouteNodeProperties = KonnectRouteNodeProperties()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            KonnectRouteToControlPlaneRel(),
            KonnectRouteToServiceRel(),
        ],
    )
