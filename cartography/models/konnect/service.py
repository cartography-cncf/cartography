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
class KonnectServiceNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef('id')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)
    name: PropertyRef = PropertyRef('name')
    host: PropertyRef = PropertyRef('host')
    port: PropertyRef = PropertyRef('port')
    protocol: PropertyRef = PropertyRef('protocol')
    path: PropertyRef = PropertyRef('path')
    enabled: PropertyRef = PropertyRef('enabled')
    connect_timeout: PropertyRef = PropertyRef('connect_timeout')
    read_timeout: PropertyRef = PropertyRef('read_timeout')
    write_timeout: PropertyRef = PropertyRef('write_timeout')
    retries: PropertyRef = PropertyRef('retries')
    created_at: PropertyRef = PropertyRef('created_at')
    updated_at: PropertyRef = PropertyRef('updated_at')


@dataclass(frozen=True)
class KonnectServiceToControlPlaneRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class KonnectServiceToControlPlaneRel(CartographyRelSchema):
    target_node_label: str = 'KonnectControlPlane'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('CONTROL_PLANE_ID', set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RESOURCE"
    properties: KonnectServiceToControlPlaneRelProperties = KonnectServiceToControlPlaneRelProperties()


@dataclass(frozen=True)
class KonnectServiceSchema(CartographyNodeSchema):
    label: str = 'KonnectService'
    properties: KonnectServiceNodeProperties = KonnectServiceNodeProperties()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            KonnectServiceToControlPlaneRel(),
        ],
    )
