from dataclasses import dataclass

from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.common import PropertyRef
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class KubernetesNamespaceNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef('id')
    name: PropertyRef = PropertyRef('name')
    created_at: PropertyRef = PropertyRef('created_at')
    deleted_at: PropertyRef = PropertyRef('deleted_at')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)
    firstseen: PropertyRef = PropertyRef('firstseen', set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesNamespaceToKubernetesClusterProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
# (:KubernetesNamespace)<-[:RESOURCE]-(:KubernetesCluster)
class KubernetesNamespaceToKubernetesCluster(CartographyRelSchema):
    target_node_label: str = 'KubernetesCluster'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('KubernetesCluster_ID', set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = 'RESOURCE'
    properties: KubernetesNamespaceToKubernetesClusterProperties = KubernetesNamespaceToKubernetesClusterProperties()


@dataclass(frozen=True)
class KubernetesNamespaceNodeSchema(CartographyNodeSchema):
    label: str = 'KubernetesNamespace'
    properties: KubernetesNamespaceNodeProperties = KubernetesNamespaceNodeProperties()
    sub_resource_relationship = None
