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
class KubernetesJobNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("uid", description="UID of the Kubernetes Job.")
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Name of the Kubernetes Job."
    )
    namespace: PropertyRef = PropertyRef(
        "namespace",
        extra_index=True,
        description="Kubernetes namespace containing the Job.",
    )
    creation_timestamp: PropertyRef = PropertyRef(
        "creation_timestamp",
        description="Timestamp when the Kubernetes Job was created.",
    )
    deletion_timestamp: PropertyRef = PropertyRef(
        "deletion_timestamp",
        description="Timestamp when the Kubernetes Job was marked for deletion.",
    )
    completions: PropertyRef = PropertyRef(
        "completions",
        description="Desired number of successfully completed pods.",
    )
    parallelism: PropertyRef = PropertyRef(
        "parallelism", description="Maximum number of pods that may run in parallel."
    )
    active: PropertyRef = PropertyRef(
        "active", description="Number of pods currently running for the Job."
    )
    succeeded: PropertyRef = PropertyRef(
        "succeeded", description="Number of pods that completed successfully."
    )
    failed: PropertyRef = PropertyRef(
        "failed", description="Number of pods that completed unsuccessfully."
    )
    labels: PropertyRef = PropertyRef(
        "labels",
        description="Metadata labels on the Job, stored as a JSON-encoded string.",
    )
    cluster_name: PropertyRef = PropertyRef(
        "CLUSTER_NAME",
        set_in_kwargs=True,
        extra_index=True,
        description="Name of the Kubernetes cluster containing the Job.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesJobToKubernetesClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KubernetesJob)<-[:RESOURCE]-(:KubernetesCluster)
class KubernetesJobToKubernetesClusterRel(CartographyRelSchema):
    """Links a cluster to one of its jobs."""

    target_node_label: str = "KubernetesCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("CLUSTER_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: KubernetesJobToKubernetesClusterRelProperties = (
        KubernetesJobToKubernetesClusterRelProperties()
    )


@dataclass(frozen=True)
class KubernetesJobToKubernetesCronJobWorkloadParentRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KubernetesJob)-[:WORKLOAD_PARENT]->(:KubernetesCronJob)
# Only fires when the Job is owned by a CronJob (the loader sets
# `_workload_parent_cronjob_id` from the Job's controller ownerReference).
# Standalone Jobs fall through to the namespace edge below.
class KubernetesJobToKubernetesCronJobWorkloadParentRel(CartographyRelSchema):
    """Links a job to the cron job that created it."""

    target_node_label: str = "KubernetesCronJob"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("_workload_parent_cronjob_id")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "WORKLOAD_PARENT"
    properties: KubernetesJobToKubernetesCronJobWorkloadParentRelProperties = (
        KubernetesJobToKubernetesCronJobWorkloadParentRelProperties()
    )


@dataclass(frozen=True)
class KubernetesJobToKubernetesNamespaceWorkloadParentRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KubernetesJob)-[:WORKLOAD_PARENT]->(:KubernetesNamespace)
# Fallback parent for standalone Jobs (no owning CronJob). The matcher is gated
# on `_workload_parent_namespace_name`, which the loader sets only when the Job
# has no CronJob owner, so CronJob-owned Jobs don't get a duplicate edge.
class KubernetesJobToKubernetesNamespaceWorkloadParentRel(CartographyRelSchema):
    """Links a job to the namespace that owns it."""

    target_node_label: str = "KubernetesNamespace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "cluster_name": PropertyRef("CLUSTER_NAME", set_in_kwargs=True),
            "name": PropertyRef("_workload_parent_namespace_name"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "WORKLOAD_PARENT"
    properties: KubernetesJobToKubernetesNamespaceWorkloadParentRelProperties = (
        KubernetesJobToKubernetesNamespaceWorkloadParentRelProperties()
    )


@dataclass(frozen=True)
class KubernetesJobSchema(CartographyNodeSchema):
    "A Kubernetes Job that runs pods to completion."

    label: str = "KubernetesJob"
    # ComputeService is the cross-provider "logical workload / controller" label.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([COMPUTE_SERVICE])
    properties: KubernetesJobNodeProperties = KubernetesJobNodeProperties()
    sub_resource_relationship: KubernetesJobToKubernetesClusterRel = (
        KubernetesJobToKubernetesClusterRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            KubernetesJobToKubernetesCronJobWorkloadParentRel(),
            KubernetesJobToKubernetesNamespaceWorkloadParentRel(),
        ]
    )
