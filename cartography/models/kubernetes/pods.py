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
class KubernetesPodNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("uid", description="UID of the Kubernetes pod.")
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Name of the Kubernetes pod."
    )
    status_phase: PropertyRef = PropertyRef(
        "status_phase",
        description="The phase of a Pod is a simple, high-level summary of where the Pod is in its lifecycle.",
    )
    creation_timestamp: PropertyRef = PropertyRef(
        "creation_timestamp",
        description="Timestamp of the creation time of the Kubernetes pod.",
    )
    deletion_timestamp: PropertyRef = PropertyRef(
        "deletion_timestamp",
        description="Timestamp of the deletion time of the Kubernetes pod.",
    )
    namespace: PropertyRef = PropertyRef(
        "namespace",
        extra_index=True,
        description="The Kubernetes namespace where this pod is deployed.",
    )
    service_account_name: PropertyRef = PropertyRef(
        "service_account_name",
        description="Name of the ServiceAccount used by the pod. Derived from `pod.spec.service_account_name` and defaults to `default` when unset.",
    )
    automount_service_account_token: PropertyRef = PropertyRef(
        "automount_service_account_token",
        description="Pod-level override for whether a service account token is automatically mounted. Derived from `pod.spec.automount_service_account_token`.",
    )
    host_pid: PropertyRef = PropertyRef(
        "host_pid",
        description="Whether the pod shares the host PID namespace. Derived from `pod.spec.host_pid`.",
    )
    host_ipc: PropertyRef = PropertyRef(
        "host_ipc",
        description="Whether the pod shares the host IPC namespace. Derived from `pod.spec.host_ipc`.",
    )
    host_network: PropertyRef = PropertyRef(
        "host_network",
        extra_index=True,
        description="Whether the pod shares the host network namespace. Derived from `pod.spec.host_network`.",
    )
    seccomp_profile_type: PropertyRef = PropertyRef(
        "seccomp_profile_type",
        description="Pod-level seccomp profile type when set, such as `RuntimeDefault`. Derived from `pod.spec.security_context.seccomp_profile.type`.",
    )
    host_path_volume_paths: PropertyRef = PropertyRef(
        "host_path_volume_paths",
        description="List of host filesystem paths mounted via `hostPath` pod volumes. Derived from `pod.spec.volumes[].host_path.path`.",
    )
    labels: PropertyRef = PropertyRef(
        "labels",
        description="Labels are key-value pairs contained in the `PodSpec` and fetched from `pod.metadata.labels`. Stored as a JSON-encoded string.",
    )
    cluster_name: PropertyRef = PropertyRef(
        "CLUSTER_NAME",
        set_in_kwargs=True,
        extra_index=True,
        description="Name of the Kubernetes cluster where this pod is deployed.",
    )
    node: PropertyRef = PropertyRef(
        "node",
        description="Name of the Kubernetes node where this pod is currently scheduled and running. Fetched from `pod.spec.node_name`.",
    )
    architecture_normalized: PropertyRef = PropertyRef(
        "architecture_normalized",
        description="Canonical CPU architecture derived from the scheduled node when available (e.g. `amd64`, `arm64`).",
    )
    exposed_internet: PropertyRef = PropertyRef(
        "exposed_internet",
        extra_index=True,
        description="Set by analysis job. `true` if this pod is reachable from an internet-facing load balancer.",
    )  # Populated by the Kubernetes compute exposure analysis job.
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )


@dataclass(frozen=True)
class KubernetesPodToKubernetesNamespaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# DEPRECATED: replaced by WORKLOAD_PARENT, will be removed in v1.0.0
@dataclass(frozen=True)
# (:KubernetesPod)<-[:CONTAINS]-(:KubernetesNamespace)
class KubernetesPodToKubernetesNamespaceRel(CartographyRelSchema):
    "Links `KubernetesNamespace` to `KubernetesPod` with `CONTAINS`."

    target_node_label: str = "KubernetesNamespace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "cluster_name": PropertyRef("CLUSTER_NAME", set_in_kwargs=True),
            "name": PropertyRef("namespace"),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: KubernetesPodToKubernetesNamespaceRelProperties = (
        KubernetesPodToKubernetesNamespaceRelProperties()
    )


@dataclass(frozen=True)
class KubernetesPodToKubernetesNamespaceWorkloadParentRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KubernetesPod)-[:WORKLOAD_PARENT]->(:KubernetesNamespace)
class KubernetesPodToKubernetesNamespaceWorkloadParentRel(CartographyRelSchema):
    "Links `KubernetesPod` to `KubernetesNamespace` with `WORKLOAD_PARENT`."

    target_node_label: str = "KubernetesNamespace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "cluster_name": PropertyRef("CLUSTER_NAME", set_in_kwargs=True),
            "name": PropertyRef("namespace"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "WORKLOAD_PARENT"
    properties: KubernetesPodToKubernetesNamespaceWorkloadParentRelProperties = (
        KubernetesPodToKubernetesNamespaceWorkloadParentRelProperties()
    )


@dataclass(frozen=True)
class KubernetesPodToKubernetesClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KubernetesPod)<-[:RESOURCE]-(:KubernetesCluster)
class KubernetesPodToKubernetesClusterRel(CartographyRelSchema):
    "Links `KubernetesCluster` to `KubernetesPod` with `RESOURCE`."

    target_node_label: str = "KubernetesCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("CLUSTER_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: KubernetesPodToKubernetesClusterRelProperties = (
        KubernetesPodToKubernetesClusterRelProperties()
    )


@dataclass(frozen=True)
class KubernetesPodToSecretRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# DEPRECATED: replaced by the canonical (:ComputePod)-[:USES_SECRET]->(:Secret)
# edge (KubernetesPodToSecretVolumeUsesSecretRel), which carries the mount
# method as the `mount_method` property. Kept for backward compatibility, will
# be removed in v1.0.0.
# (:KubernetesPod)-[:USES_SECRET_VOLUME]->(:KubernetesSecret)
class KubernetesPodToSecretVolumeRel(CartographyRelSchema):
    "Links `KubernetesPod` to `KubernetesSecret` with `USES_SECRET_VOLUME`."

    target_node_label: str = "KubernetesSecret"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "composite_id": PropertyRef("secret_volume_ids", one_to_many=True),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_SECRET_VOLUME"
    properties: KubernetesPodToSecretRelProperties = (
        KubernetesPodToSecretRelProperties()
    )


@dataclass(frozen=True)
# DEPRECATED: replaced by the canonical (:ComputePod)-[:USES_SECRET]->(:Secret)
# edge (KubernetesPodToSecretEnvUsesSecretRel), which carries the mount method
# as the `mount_method` property. Kept for backward compatibility, will be
# removed in v1.0.0.
# (:KubernetesPod)-[:USES_SECRET_ENV]->(:KubernetesSecret)
class KubernetesPodToSecretEnvRel(CartographyRelSchema):
    "Links `KubernetesPod` to `KubernetesSecret` with `USES_SECRET_ENV`."

    target_node_label: str = "KubernetesSecret"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "composite_id": PropertyRef("secret_env_ids", one_to_many=True),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_SECRET_ENV"
    properties: KubernetesPodToSecretRelProperties = (
        KubernetesPodToSecretRelProperties()
    )


# The canonical USES_SECRET edge collapses the volume/env distinction into a
# single (:ComputePod)-[:USES_SECRET]->(:Secret) edge carrying the injection
# method on the `mount_method` property. To avoid one method overwriting the
# other when a pod uses the same secret both ways, the source id lists are
# disjoint (volume-only, env-only, both), so each edge is written exactly once.
@dataclass(frozen=True)
class KubernetesPodToSecretVolumeUsesSecretRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    mount_method: PropertyRef = PropertyRef(
        "secret_mount_volume",
        set_in_kwargs=True,
        description="How the pod consumes the secret: volume, environment, or both.",
    )


@dataclass(frozen=True)
# Canonical ontology edge: (:ComputePod)-[:USES_SECRET]->(:Secret), mount_method="volume"
class KubernetesPodToSecretVolumeUsesSecretRel(CartographyRelSchema):
    "Links `KubernetesPod` to `KubernetesSecret` with `USES_SECRET`."

    target_node_label: str = "KubernetesSecret"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "composite_id": PropertyRef(
                "secret_uses_volume_only_ids", one_to_many=True
            ),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_SECRET"
    properties: KubernetesPodToSecretVolumeUsesSecretRelProperties = (
        KubernetesPodToSecretVolumeUsesSecretRelProperties()
    )


@dataclass(frozen=True)
class KubernetesPodToSecretEnvUsesSecretRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    mount_method: PropertyRef = PropertyRef(
        "secret_mount_env",
        set_in_kwargs=True,
        description="How the pod consumes the secret: volume, environment, or both.",
    )


@dataclass(frozen=True)
# Canonical ontology edge: (:ComputePod)-[:USES_SECRET]->(:Secret), mount_method="env"
class KubernetesPodToSecretEnvUsesSecretRel(CartographyRelSchema):
    "Links `KubernetesPod` to `KubernetesSecret` with `USES_SECRET`."

    target_node_label: str = "KubernetesSecret"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "composite_id": PropertyRef("secret_uses_env_only_ids", one_to_many=True),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_SECRET"
    properties: KubernetesPodToSecretEnvUsesSecretRelProperties = (
        KubernetesPodToSecretEnvUsesSecretRelProperties()
    )


@dataclass(frozen=True)
class KubernetesPodToSecretBothUsesSecretRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    mount_method: PropertyRef = PropertyRef(
        "secret_mount_both",
        set_in_kwargs=True,
        description="How the pod consumes the secret: volume, environment, or both.",
    )


@dataclass(frozen=True)
# Canonical ontology edge: (:ComputePod)-[:USES_SECRET]->(:Secret),
# mount_method="volume,env" for secrets consumed both as a volume and via env.
class KubernetesPodToSecretBothUsesSecretRel(CartographyRelSchema):
    "Links `KubernetesPod` to `KubernetesSecret` with `USES_SECRET`."

    target_node_label: str = "KubernetesSecret"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "composite_id": PropertyRef("secret_uses_both_ids", one_to_many=True),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_SECRET"
    properties: KubernetesPodToSecretBothUsesSecretRelProperties = (
        KubernetesPodToSecretBothUsesSecretRelProperties()
    )


@dataclass(frozen=True)
class KubernetesPodToKubernetesNodeRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KubernetesPod)-[:RUNS_ON]->(:KubernetesNode)
class KubernetesPodToKubernetesNodeRel(CartographyRelSchema):
    "Links `KubernetesPod` to `KubernetesNode` with `RUNS_ON`."

    target_node_label: str = "KubernetesNode"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("node_id")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RUNS_ON"
    properties: KubernetesPodToKubernetesNodeRelProperties = (
        KubernetesPodToKubernetesNodeRelProperties()
    )


@dataclass(frozen=True)
class KubernetesPodToServiceAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# DEPRECATED: replaced by the canonical (:ComputePod)-[:RUNS_AS]->(:ServiceAccount)
# edge (KubernetesPodToServiceAccountRunsAsRel). Kept for backward
# compatibility, will be removed in v1.0.0.
# (:KubernetesPod)-[:USES_SERVICE_ACCOUNT]->(:KubernetesServiceAccount)
class KubernetesPodToServiceAccountRel(CartographyRelSchema):
    "Links `KubernetesPod` to `KubernetesServiceAccount` with `USES_SERVICE_ACCOUNT`."

    target_node_label: str = "KubernetesServiceAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("service_account_id"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_SERVICE_ACCOUNT"
    properties: KubernetesPodToServiceAccountRelProperties = (
        KubernetesPodToServiceAccountRelProperties()
    )


@dataclass(frozen=True)
class KubernetesPodToServiceAccountRunsAsRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# Canonical ontology edge: (:ComputePod)-[:RUNS_AS]->(:ServiceAccount)
class KubernetesPodToServiceAccountRunsAsRel(CartographyRelSchema):
    "Links `KubernetesPod` to `KubernetesServiceAccount` with `RUNS_AS`."

    target_node_label: str = "KubernetesServiceAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("service_account_id"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RUNS_AS"
    properties: KubernetesPodToServiceAccountRunsAsRelProperties = (
        KubernetesPodToServiceAccountRunsAsRelProperties()
    )


@dataclass(frozen=True)
class KubernetesPodSchema(CartographyNodeSchema):
    "A Kubernetes pod and its workload security configuration."

    label: str = "KubernetesPod"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["ComputePod"])
    properties: KubernetesPodNodeProperties = KubernetesPodNodeProperties()
    sub_resource_relationship: KubernetesPodToKubernetesClusterRel = (
        KubernetesPodToKubernetesClusterRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            KubernetesPodToKubernetesNamespaceRel(),
            KubernetesPodToKubernetesNamespaceWorkloadParentRel(),
            KubernetesPodToKubernetesNodeRel(),
            KubernetesPodToServiceAccountRel(),
            KubernetesPodToServiceAccountRunsAsRel(),
            KubernetesPodToSecretVolumeRel(),
            KubernetesPodToSecretEnvRel(),
            KubernetesPodToSecretVolumeUsesSecretRel(),
            KubernetesPodToSecretEnvUsesSecretRel(),
            KubernetesPodToSecretBothUsesSecretRel(),
        ]
    )
