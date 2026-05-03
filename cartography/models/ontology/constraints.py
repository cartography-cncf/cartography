from dataclasses import dataclass

from cartography.models.aws.ecs.containers import ECSContainerToTaskRel
from cartography.models.aws.ecs.services import ECSServiceToECSClusterRel
from cartography.models.aws.ecs.services import ECSServiceToECSTaskRel
from cartography.models.aws.ecs.tasks import ECSTaskToECSClusterRel
from cartography.models.azure.container_instance import (
    AzureGroupContainerToContainerInstanceRel,
)
from cartography.models.gcp.cloudrun.job_container import CloudRunJobToContainerRel
from cartography.models.gcp.cloudrun.service_container import (
    CloudRunServiceToContainerRel,
)
from cartography.models.kubernetes.containers import (
    KubernetesContainerToKubernetesPodRel,
)
from cartography.models.kubernetes.namespaces import (
    KubernetesNamespaceToKubernetesClusterRel,
)
from cartography.models.kubernetes.pods import KubernetesPodToKubernetesClusterRel
from cartography.models.kubernetes.pods import KubernetesPodToKubernetesNamespaceRel


@dataclass(frozen=True)
class RelConstraint:
    """If a node carrying ontology label `src` has an outward edge toward a
    node carrying ontology label `dst`, that edge MUST be named `label`.

    The constraint never requires the edge to exist; it only constrains the
    name when both endpoints carry the listed ontology labels. Both abstract
    ontology nodes (User, Device, PublicIP, Package) and semantic extra
    labels (Container, ComputePod, ...) are valid src/dst values.
    """

    src: str
    dst: str
    label: str


# Canonical relationship names enforced by test_ontology_rel_constraints.
ONTOLOGY_REL_CONSTRAINTS: tuple[RelConstraint, ...] = (
    # User has one or many UserAccount on different platforms.
    RelConstraint(src="User", dst="UserAccount", label="HAS_ACCOUNT"),
    # Unified workload chain: child workload points at its parent.
    RelConstraint(src="Container", dst="ComputePod", label="WORKLOAD_PARENT"),
    RelConstraint(src="Container", dst="ComputeService", label="WORKLOAD_PARENT"),
    RelConstraint(src="ComputePod", dst="ComputeService", label="WORKLOAD_PARENT"),
    RelConstraint(src="ComputePod", dst="ComputeNamespace", label="WORKLOAD_PARENT"),
    RelConstraint(src="ComputePod", dst="ComputeCluster", label="WORKLOAD_PARENT"),
    RelConstraint(src="ComputeService", dst="ComputeCluster", label="WORKLOAD_PARENT"),
    RelConstraint(
        src="ComputeNamespace", dst="ComputeCluster", label="WORKLOAD_PARENT"
    ),
)


# DEPRECATED: pre-V1 rel classes tolerated until they are removed in v1.0.0.
LEGACY_REL_WHITELIST: frozenset[type] = frozenset(
    {
        # DEPRECATED: replaced by WORKLOAD_PARENT, will be removed in v1.0.0.
        AzureGroupContainerToContainerInstanceRel,
        CloudRunJobToContainerRel,
        CloudRunServiceToContainerRel,
        ECSContainerToTaskRel,
        ECSServiceToECSClusterRel,
        ECSServiceToECSTaskRel,
        ECSTaskToECSClusterRel,
        KubernetesContainerToKubernetesPodRel,
        KubernetesPodToKubernetesNamespaceRel,
        # Kubernetes models its cluster as the tenant, so the pod's and
        # namespace's sub_resource_relationship uses RESOURCE on a pair that
        # the ontology also constrains as WORKLOAD_PARENT. Whitelisted until
        # tenant scoping and the workload chain are reconciled.
        KubernetesNamespaceToKubernetesClusterRel,
        KubernetesPodToKubernetesClusterRel,
    }
)
