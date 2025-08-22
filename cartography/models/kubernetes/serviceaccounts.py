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
class KubernetesServiceAccountNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    namespace: PropertyRef = PropertyRef("namespace")
    uid: PropertyRef = PropertyRef("uid")
    creation_timestamp: PropertyRef = PropertyRef("creation_timestamp")
    resource_version: PropertyRef = PropertyRef("resource_version")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesServiceAccountToNamespaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesServiceAccountToNamespaceRel(CartographyRelSchema):
    target_node_label: str = "KubernetesNamespace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "cluster_name": PropertyRef("CLUSTER_NAME", set_in_kwargs=True),
            "name": PropertyRef("namespace"),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: KubernetesServiceAccountToNamespaceRelProperties = (
        KubernetesServiceAccountToNamespaceRelProperties()
    )


@dataclass(frozen=True)
class KubernetesServiceAccountToClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesServiceAccountToClusterRel(CartographyRelSchema):
    target_node_label: str = "KubernetesCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("CLUSTER_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: KubernetesServiceAccountToClusterRelProperties = (
        KubernetesServiceAccountToClusterRelProperties()
    )


@dataclass(frozen=True)
class KubernetesServiceAccountSchema(CartographyNodeSchema):
    label: str = "KubernetesServiceAccount"
    properties: KubernetesServiceAccountNodeProperties = (
        KubernetesServiceAccountNodeProperties()
    )
    sub_resource_relationship: KubernetesServiceAccountToClusterRel = (
        KubernetesServiceAccountToClusterRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            KubernetesServiceAccountToNamespaceRel(),
        ]
    )
