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
class KubernetesContainerNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "uid",
        description="Identifier for the container which is derived from the UID of pod and the name of container.",
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Name of the container in kubernetes pod."
    )
    image: PropertyRef = PropertyRef(
        "image", extra_index=True, description="Docker image used in the container."
    )
    namespace: PropertyRef = PropertyRef(
        "namespace",
        extra_index=True,
        description="The Kubernetes namespace where this container is deployed.",
    )
    cluster_name: PropertyRef = PropertyRef(
        "CLUSTER_NAME",
        set_in_kwargs=True,
        extra_index=True,
        description="Name of the Kubernetes cluster where this container is deployed.",
    )
    region: PropertyRef = PropertyRef(
        "REGION",
        set_in_kwargs=True,
        description="Cloud region associated with the Kubernetes cluster.",
    )
    image_pull_policy: PropertyRef = PropertyRef(
        "image_pull_policy",
        description="The policy that determines when the kubelet attempts to pull the specified image (Always, Never, IfNotPresent).",
    )
    status_image_id: PropertyRef = PropertyRef(
        "status_image_id",
        description="Runtime-reported image identifier for the container. This may differ from the declared `image` field because the container runtime can rewrite tags or parent image indexes to digest-qualified references.",
    )
    status_image_sha: PropertyRef = PropertyRef(
        "status_image_sha",
        extra_index=True,
        description="The SHA portion of the runtime-reported `status_image_id` when Cartography can extract it.",
    )
    status_ready: PropertyRef = PropertyRef(
        "status_ready",
        description="Specifies whether the container has passed its readiness probe.",
    )
    status_started: PropertyRef = PropertyRef(
        "status_started",
        description="Specifies whether the container has passed its startup probe.",
    )
    status_state: PropertyRef = PropertyRef(
        "status_state",
        extra_index=True,
        description="State of the container (running, terminated, waiting).",
    )
    memory_request: PropertyRef = PropertyRef(
        "memory_request",
        description='Minimum amount of memory guaranteed to be available to the container (e.g. "128Mi", "1Gi").',
    )
    cpu_request: PropertyRef = PropertyRef(
        "cpu_request",
        description='Minimum amount of CPU guaranteed to be available to the container (e.g. "100m", "1").',
    )
    memory_limit: PropertyRef = PropertyRef(
        "memory_limit",
        description='Maximum amount of memory the container is allowed to use (e.g. "256Mi", "2Gi").',
    )
    cpu_limit: PropertyRef = PropertyRef(
        "cpu_limit",
        description='Maximum amount of CPU the container is allowed to use (e.g. "500m", "2").',
    )
    allow_privilege_escalation: PropertyRef = PropertyRef(
        "allow_privilege_escalation",
        description="Whether the container explicitly allows privilege escalation. Derived from `container.security_context.allow_privilege_escalation`.",
    )
    run_as_non_root: PropertyRef = PropertyRef(
        "run_as_non_root",
        description="Whether the container is configured to run as non-root. Derived from `container.security_context.run_as_non_root`.",
    )
    run_as_user: PropertyRef = PropertyRef(
        "run_as_user",
        description="Explicit UID configured for the container. Derived from `container.security_context.run_as_user`.",
    )
    seccomp_profile_type: PropertyRef = PropertyRef(
        "seccomp_profile_type",
        description="Container-level seccomp profile type when set, such as `RuntimeDefault`. Derived from `container.security_context.seccomp_profile.type`.",
    )
    added_capabilities: PropertyRef = PropertyRef(
        "added_capabilities",
        description="Linux capabilities explicitly added to the container. Derived from `container.security_context.capabilities.add`.",
    )
    dropped_capabilities: PropertyRef = PropertyRef(
        "dropped_capabilities",
        description="Linux capabilities explicitly dropped by the container. Derived from `container.security_context.capabilities.drop`.",
    )
    host_ports: PropertyRef = PropertyRef(
        "host_ports",
        description="List of host ports exposed by the container. Derived from `container.ports[].host_port`.",
    )
    container_ports: PropertyRef = PropertyRef(
        "container_ports",
        description="The ports the container *declares* in its pod spec. Derived from `container.ports[]`, stored as a JSON-encoded list of `{container_port, protocol, name}`. `containerPort` is optional in Kubernetes, so this reflects declared ports only, not necessarily every port the process listens on.",
    )
    container_port_numbers: PropertyRef = PropertyRef(
        "container_port_numbers",
        extra_index=True,
        description="Flat, queryable list of the declared TCP/UDP `containerPort` numbers. Derived from `container.ports[].container_port`. An empty list means the container *declares* no ports; it is not proof that the container listens on nothing, since a process can bind ports it never declared.",
    )
    architecture_normalized: PropertyRef = PropertyRef(
        "architecture_normalized",
        description="Canonical CPU architecture derived from the scheduled node when available (e.g. `amd64`, `arm64`).",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )


@dataclass(frozen=True)
class KubernetesContainerToKubernetesNamespaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesContainerToKubernetesPodRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KubernetesContainer)<-[:CONTAINS]-(:KubernetesNamespace)
class KubernetesContainerToKubernetesNamespaceRel(CartographyRelSchema):
    "Links `KubernetesNamespace` to `KubernetesContainer` with `CONTAINS`."

    target_node_label: str = "KubernetesNamespace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "cluster_name": PropertyRef("CLUSTER_NAME", set_in_kwargs=True),
            "name": PropertyRef("namespace"),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: KubernetesContainerToKubernetesNamespaceRelProperties = (
        KubernetesContainerToKubernetesNamespaceRelProperties()
    )


@dataclass(frozen=True)
# DEPRECATED: replaced by WORKLOAD_PARENT, will be removed in v1.0.0
# (:KubernetesContainer)<-[:CONTAINS]-(:KubernetesPod)
class KubernetesContainerToKubernetesPodRel(CartographyRelSchema):
    "Links `KubernetesPod` to `KubernetesContainer` with `CONTAINS`."

    target_node_label: str = "KubernetesPod"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "cluster_name": PropertyRef("CLUSTER_NAME", set_in_kwargs=True),
            "namespace": PropertyRef("namespace"),
            "id": PropertyRef("pod_id"),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: KubernetesContainerToKubernetesPodRelProperties = (
        KubernetesContainerToKubernetesPodRelProperties()
    )


@dataclass(frozen=True)
class KubernetesContainerToKubernetesPodWorkloadParentRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KubernetesContainer)-[:WORKLOAD_PARENT]->(:KubernetesPod)
class KubernetesContainerToKubernetesPodWorkloadParentRel(CartographyRelSchema):
    "Links `KubernetesContainer` to `KubernetesPod` with `WORKLOAD_PARENT`."

    target_node_label: str = "KubernetesPod"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "cluster_name": PropertyRef("CLUSTER_NAME", set_in_kwargs=True),
            "namespace": PropertyRef("namespace"),
            "id": PropertyRef("pod_id"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "WORKLOAD_PARENT"
    properties: KubernetesContainerToKubernetesPodWorkloadParentRelProperties = (
        KubernetesContainerToKubernetesPodWorkloadParentRelProperties()
    )


@dataclass(frozen=True)
class KubernetesContainerToKubernetesClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KubernetesContainer)<-[:RESOURCE]-(:KubernetesCluster)
class KubernetesContainerToKubernetesClusterRel(CartographyRelSchema):
    "Links `KubernetesCluster` to `KubernetesContainer` with `RESOURCE`."

    target_node_label: str = "KubernetesCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("CLUSTER_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: KubernetesContainerToKubernetesClusterRelProperties = (
        KubernetesContainerToKubernetesClusterRelProperties()
    )


@dataclass(frozen=True)
class KubernetesContainerToECRImageRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesContainerToECRImageRel(CartographyRelSchema):
    "Links `KubernetesContainer` to `AWSECRImage` with `HAS_IMAGE`."

    target_node_label: str = "AWSECRImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"digest": PropertyRef("status_image_sha")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_IMAGE"
    properties: KubernetesContainerToECRImageRelProperties = (
        KubernetesContainerToECRImageRelProperties()
    )


@dataclass(frozen=True)
class KubernetesContainerToGitLabContainerImageRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesContainerToGitLabContainerImageRel(CartographyRelSchema):
    "Links `KubernetesContainer` to `GitLabContainerImage` with `HAS_IMAGE`."

    target_node_label: str = "GitLabContainerImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"digest": PropertyRef("status_image_sha")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_IMAGE"
    properties: KubernetesContainerToGitLabContainerImageRelProperties = (
        KubernetesContainerToGitLabContainerImageRelProperties()
    )


@dataclass(frozen=True)
class KubernetesContainerToGCPArtifactRegistryImageRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesContainerToGCPArtifactRegistryImageRel(CartographyRelSchema):
    "Links `KubernetesContainer` to `GCPArtifactRegistryImage` with `HAS_IMAGE`."

    target_node_label: str = "GCPArtifactRegistryImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"digest": PropertyRef("status_image_sha")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_IMAGE"
    properties: KubernetesContainerToGCPArtifactRegistryImageRelProperties = (
        KubernetesContainerToGCPArtifactRegistryImageRelProperties()
    )


@dataclass(frozen=True)
class KubernetesContainerToGitHubContainerImageRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesContainerToGitHubContainerImageRel(CartographyRelSchema):
    "Links `KubernetesContainer` to `GitHubContainerImage` with `HAS_IMAGE`."

    target_node_label: str = "GitHubContainerImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"digest": PropertyRef("status_image_sha")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_IMAGE"
    properties: KubernetesContainerToGitHubContainerImageRelProperties = (
        KubernetesContainerToGitHubContainerImageRelProperties()
    )


@dataclass(frozen=True)
class KubernetesContainerSchema(CartographyNodeSchema):
    "A container declared by a Kubernetes pod."

    label: str = "KubernetesContainer"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Container"])
    properties: KubernetesContainerNodeProperties = KubernetesContainerNodeProperties()
    sub_resource_relationship: KubernetesContainerToKubernetesClusterRel = (
        KubernetesContainerToKubernetesClusterRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            KubernetesContainerToKubernetesNamespaceRel(),
            KubernetesContainerToKubernetesPodRel(),
            KubernetesContainerToKubernetesPodWorkloadParentRel(),
            KubernetesContainerToECRImageRel(),
            KubernetesContainerToGitLabContainerImageRel(),
            KubernetesContainerToGCPArtifactRegistryImageRel(),
            KubernetesContainerToGitHubContainerImageRel(),
        ]
    )
