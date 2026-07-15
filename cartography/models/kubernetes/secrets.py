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
class KubernetesSecretNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("uid", description="UID of the kubernetes secret.")
    composite_id: PropertyRef = PropertyRef(
        "composite_id",
        extra_index=True,
        description="Cluster, namespace, and name identifier used for matching.",
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Name of the kubernetes secret."
    )
    creation_timestamp: PropertyRef = PropertyRef(
        "creation_timestamp",
        description="Timestamp of the creation time of the kubernetes secret.",
    )
    deletion_timestamp: PropertyRef = PropertyRef(
        "deletion_timestamp",
        description="Timestamp of the deletion time of the kubernetes secret.",
    )
    namespace: PropertyRef = PropertyRef(
        "namespace",
        extra_index=True,
        description="The Kubernetes namespace where this secret is deployed.",
    )
    owner_references: PropertyRef = PropertyRef(
        "owner_references",
        description="References to objects that own this secret. Useful if a secret is an `ExternalSecret`. Fetched from `secret.metadata.owner_references`. Stored as a JSON-encoded string.",
    )
    type: PropertyRef = PropertyRef(
        "type", description="Type of kubernetes secret (e.g. `Opaque`)."
    )
    cluster_name: PropertyRef = PropertyRef(
        "CLUSTER_NAME",
        set_in_kwargs=True,
        extra_index=True,
        description="Name of the Kubernetes cluster where this secret is deployed.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )


@dataclass(frozen=True)
class KubernetesSecretToKubernetesNamespaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KubernetesSecret)<-[:CONTAINS]-(:KubernetesNamespace)
class KubernetesSecretToKubernetesNamespaceRel(CartographyRelSchema):
    "Links `KubernetesNamespace` to `KubernetesSecret` with `CONTAINS`."

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
    "Links `KubernetesCluster` to `KubernetesSecret` with `RESOURCE`."

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
    "Metadata for a Kubernetes secret without its secret content."

    label: str = "KubernetesSecret"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        ["Secret"]
    )  # Secret label is used for ontology mapping
    properties: KubernetesSecretNodeProperties = KubernetesSecretNodeProperties()
    sub_resource_relationship: KubernetesSecretToKubernetesClusterRel = (
        KubernetesSecretToKubernetesClusterRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [KubernetesSecretToKubernetesNamespaceRel()]
    )
