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
class KubernetesReplicaSetNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("uid")
    name: PropertyRef = PropertyRef("name", extra_index=True)
    namespace: PropertyRef = PropertyRef("namespace", extra_index=True)
    creation_timestamp: PropertyRef = PropertyRef("creation_timestamp")
    deletion_timestamp: PropertyRef = PropertyRef("deletion_timestamp")
    replicas: PropertyRef = PropertyRef("replicas")
    ready_replicas: PropertyRef = PropertyRef("ready_replicas")
    labels: PropertyRef = PropertyRef("labels")
    cluster_name: PropertyRef = PropertyRef(
        "CLUSTER_NAME", set_in_kwargs=True, extra_index=True
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesReplicaSetToKubernetesClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KubernetesReplicaSet)<-[:RESOURCE]-(:KubernetesCluster)
class KubernetesReplicaSetToKubernetesClusterRel(CartographyRelSchema):
    target_node_label: str = "KubernetesCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("CLUSTER_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: KubernetesReplicaSetToKubernetesClusterRelProperties = (
        KubernetesReplicaSetToKubernetesClusterRelProperties()
    )


@dataclass(frozen=True)
class KubernetesReplicaSetToKubernetesDeploymentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KubernetesReplicaSet)-[:OWNED_BY]->(:KubernetesDeployment)
# Raw Kubernetes ownerReference. The ReplicaSet is an implementation detail and
# is deliberately kept off the WORKLOAD_PARENT chain (it carries no ontology
# label), so the pod's WORKLOAD_PARENT collapses straight to the Deployment.
# Only fires when the ReplicaSet is owned by a Deployment (loader sets
# `_owner_deployment_id`); bare ReplicaSets get no edge.
class KubernetesReplicaSetToKubernetesDeploymentRel(CartographyRelSchema):
    target_node_label: str = "KubernetesDeployment"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("_owner_deployment_id")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "OWNED_BY"
    properties: KubernetesReplicaSetToKubernetesDeploymentRelProperties = (
        KubernetesReplicaSetToKubernetesDeploymentRelProperties()
    )


@dataclass(frozen=True)
class KubernetesReplicaSetSchema(CartographyNodeSchema):
    label: str = "KubernetesReplicaSet"
    # No ontology label: the ReplicaSet is collapsed out of the WORKLOAD_PARENT
    # chain, so its owning Deployment is the surfaced workload parent.
    properties: KubernetesReplicaSetNodeProperties = (
        KubernetesReplicaSetNodeProperties()
    )
    sub_resource_relationship: KubernetesReplicaSetToKubernetesClusterRel = (
        KubernetesReplicaSetToKubernetesClusterRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            KubernetesReplicaSetToKubernetesDeploymentRel(),
        ]
    )
