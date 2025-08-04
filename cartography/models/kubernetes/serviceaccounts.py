from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties, CartographyNodeSchema
from cartography.models.core.relationships import (
    CartographyRelProperties,
    CartographyRelSchema,
    LinkDirection,
    make_target_node_matcher,
    TargetNodeMatcher,
)


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
        {"name": PropertyRef("namespace")}
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
        {"id": PropertyRef("cluster_id", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: KubernetesServiceAccountToClusterRelProperties = (
        KubernetesServiceAccountToClusterRelProperties()
    )


@dataclass(frozen=True)
class KubernetesServiceAccountSchema(CartographyNodeSchema):
    label: str = "KubernetesServiceAccount"
    properties: KubernetesServiceAccountNodeProperties = KubernetesServiceAccountNodeProperties()
    sub_resource_relationship: KubernetesServiceAccountToClusterRel = KubernetesServiceAccountToClusterRel()
    other_relationships: tuple = (KubernetesServiceAccountToNamespaceRel(),) 