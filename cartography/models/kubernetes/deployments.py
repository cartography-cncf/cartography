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
from cartography.models.ontology.labels import COMPUTE_SERVICE


@dataclass(frozen=True)
class KubernetesDeploymentNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "uid", description="UID of the Kubernetes Deployment."
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Name of the Kubernetes Deployment."
    )
    namespace: PropertyRef = PropertyRef(
        "namespace",
        extra_index=True,
        description="Kubernetes namespace containing the Deployment.",
    )
    creation_timestamp: PropertyRef = PropertyRef(
        "creation_timestamp",
        description="Timestamp when the Kubernetes Deployment was created.",
    )
    deletion_timestamp: PropertyRef = PropertyRef(
        "deletion_timestamp",
        description="Timestamp when the Kubernetes Deployment was marked for deletion.",
    )
    replicas: PropertyRef = PropertyRef(
        "replicas", description="Desired number of pod replicas."
    )
    ready_replicas: PropertyRef = PropertyRef(
        "ready_replicas", description="Number of pod replicas that are ready."
    )
    available_replicas: PropertyRef = PropertyRef(
        "available_replicas",
        description="Number of pod replicas that are available.",
    )
    labels: PropertyRef = PropertyRef(
        "labels",
        description="Metadata labels on the Deployment, stored as a JSON-encoded string.",
    )
    cluster_name: PropertyRef = PropertyRef(
        "CLUSTER_NAME",
        set_in_kwargs=True,
        extra_index=True,
        description="Name of the Kubernetes cluster containing the Deployment.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesDeploymentToKubernetesClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KubernetesDeployment)<-[:RESOURCE]-(:KubernetesCluster)
class KubernetesDeploymentToKubernetesClusterRel(CartographyRelSchema):
    """Links a cluster to one of its deployments."""

    target_node_label: str = "KubernetesCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("CLUSTER_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: KubernetesDeploymentToKubernetesClusterRelProperties = (
        KubernetesDeploymentToKubernetesClusterRelProperties()
    )


@dataclass(frozen=True)
class KubernetesDeploymentToKubernetesNamespaceWorkloadParentRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KubernetesDeployment)-[:WORKLOAD_PARENT]->(:KubernetesNamespace)
class KubernetesDeploymentToKubernetesNamespaceWorkloadParentRel(CartographyRelSchema):
    """Links a deployment to the namespace that owns it."""

    target_node_label: str = "KubernetesNamespace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "cluster_name": PropertyRef("CLUSTER_NAME", set_in_kwargs=True),
            "name": PropertyRef("namespace"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "WORKLOAD_PARENT"
    properties: KubernetesDeploymentToKubernetesNamespaceWorkloadParentRelProperties = (
        KubernetesDeploymentToKubernetesNamespaceWorkloadParentRelProperties()
    )


@dataclass(frozen=True)
class KubernetesDeploymentSchema(CartographyNodeSchema):
    "A Kubernetes Deployment that manages a replicated application workload."

    label: str = "KubernetesDeployment"
    # ComputeService is the cross-provider "logical workload / controller" label
    # (peer of AWSECSService, GCPCloudRunService). It makes the Deployment the
    # surfaced parent in the WORKLOAD_PARENT chain above the pod.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([COMPUTE_SERVICE])
    properties: KubernetesDeploymentNodeProperties = (
        KubernetesDeploymentNodeProperties()
    )
    sub_resource_relationship: KubernetesDeploymentToKubernetesClusterRel = (
        KubernetesDeploymentToKubernetesClusterRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            KubernetesDeploymentToKubernetesNamespaceWorkloadParentRel(),
        ]
    )
