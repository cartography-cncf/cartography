from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class ELBListenerNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef('id')
    port: PropertyRef = PropertyRef('port')
    protocol: PropertyRef = PropertyRef('protocol')
    instance_port: PropertyRef = PropertyRef('instance_port')
    instance_protocol: PropertyRef = PropertyRef('instance_protocol')
    policy_names: PropertyRef = PropertyRef('policy_names')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class ELBListenerToLoadBalancerRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class ELBListenerToLoadBalancer(CartographyRelSchema):
    target_node_label: str = 'LoadBalancer'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('LoadBalancerId')},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "ELB_LISTENER"
    properties: ELBListenerToLoadBalancerRelProperties = ELBListenerToLoadBalancerRelProperties()


@dataclass(frozen=True)
class ELBListenerSchema(CartographyNodeSchema):
    label: str = 'ELBListener'
    properties: ELBListenerNodeProperties = ELBListenerNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(['Endpoint'])
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ELBListenerToLoadBalancer(),
        ],
    )
