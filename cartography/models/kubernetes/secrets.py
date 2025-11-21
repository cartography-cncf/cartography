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
class KubernetesSecretNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("uid")
    name: PropertyRef = PropertyRef("name", extra_index=True)
    creation_timestamp: PropertyRef = PropertyRef("creation_timestamp")
    deletion_timestamp: PropertyRef = PropertyRef("deletion_timestamp")
    namespace: PropertyRef = PropertyRef("namespace", extra_index=True)
    owner_references: PropertyRef = PropertyRef("owner_references")
    type: PropertyRef = PropertyRef("type")
    cluster_name: PropertyRef = PropertyRef(
        "CLUSTER_NAME", set_in_kwargs=True, extra_index=True
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesSecretToKubernetesNamespaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KubernetesSecret)<-[:CONTAINS]-(:KubernetesNamespace)
class KubernetesSecretToKubernetesNamespaceRel(CartographyRelSchema):
    target_node_label: str = "KubernetesNamespace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "cluster_name": PropertyRef("CLUSTER_NAME", set_in_kwargs=True),
            "name": PropertyRef("namespace"),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: KubernetesSecretToKubernetesNamespaceRelProperties = (
        KubernetesSecretToKubernetesNamespaceRelProperties()
    )


@dataclass(frozen=True)
class KubernetesSecretToKubernetesClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KubernetesSecret)<-[:RESOURCE]-(:KubernetesCluster)
class KubernetesSecretToKubernetesClusterRel(CartographyRelSchema):
    target_node_label: str = "KubernetesCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("CLUSTER_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: KubernetesSecretToKubernetesClusterRelProperties = (
        KubernetesSecretToKubernetesClusterRelProperties()
    )


@dataclass(frozen=True)
class KubernetesSecretSchema(CartographyNodeSchema):
    label: str = "KubernetesSecret"
    properties: KubernetesSecretNodeProperties = KubernetesSecretNodeProperties()
    sub_resource_relationship: KubernetesSecretToKubernetesClusterRel = (
        KubernetesSecretToKubernetesClusterRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [KubernetesSecretToKubernetesNamespaceRel()]
    )
