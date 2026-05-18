"""
CIS Kubernetes Workload and General Policy Security Checks

Implements CIS Kubernetes Benchmark Sections 5.4 and 5.6
Based on CIS Kubernetes Benchmark v1.12.0

Section 5.4: Secrets Management
Section 5.6: General Policies
"""

from cartography.rules.data.frameworks.cis import cis_kubernetes
from cartography.rules.data.frameworks.iso27001 import iso27001_annex_a
from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule
from cartography.rules.spec.model import RuleReference

CIS_REFERENCES = [
    RuleReference(
        text="CIS Kubernetes Benchmark v1.12.0",
        url="https://www.cisecurity.org/benchmark/kubernetes",
    ),
    RuleReference(
        text="Kubernetes Security Best Practices",
        url="https://kubernetes.io/docs/concepts/security/",
    ),
]


# =============================================================================
# CIS K8s 5.4.1: Prefer using secrets as files over env vars
# Main node: KubernetesPod
# =============================================================================
class SecretsInEnvVarsOutput(Finding):
    """Output model for secrets in environment variables check."""

    pod_name: str | None = None
    pod_id: str | None = None
    namespace: str | None = None
    secret_names: list[str] | None = None
    cluster_name: str | None = None


_k8s_secrets_in_env_vars = Fact(
    id="k8s_secrets_in_env_vars",
    name="Kubernetes pods using secrets via environment variables",
    description=(
        "Detects pods that reference secrets through environment variables. "
        "Secrets as environment variables are more susceptible to accidental exposure "
        "through logging, error messages, or child process inheritance. "
        "Prefer mounting secrets as files instead."
    ),
    cypher_query="""
    MATCH (cluster:KubernetesCluster)-[:RESOURCE]->(pod:KubernetesPod)
          -[:USES_SECRET_ENV]->(secret:KubernetesSecret)
    RETURN
        pod.id AS pod_id,
        pod.name AS pod_name,
        pod.namespace AS namespace,
        collect(DISTINCT secret.name) AS secret_names,
        cluster.name AS cluster_name
    """,
    cypher_visual_query="""
    MATCH p=(cluster:KubernetesCluster)-[:RESOURCE]->(pod:KubernetesPod)
          -[:USES_SECRET_ENV]->(secret:KubernetesSecret)
    RETURN *
    """,
    cypher_count_query="""
    MATCH (pod:KubernetesPod)
    RETURN COUNT(pod) AS count
    """,
    asset_id_field="pod_id",
    module=Module.KUBERNETES,
    maturity=Maturity.EXPERIMENTAL,
)

cis_k8s_5_4_1_secrets_in_env_vars = Rule(
    id="cis_k8s_5_4_1_secrets_in_env_vars",
    name="CIS K8s 5.4.1: Secrets Used as Environment Variables",
    description=(
        "Secrets should be mounted as files rather than exposed as environment variables. "
        "Environment variables are more susceptible to accidental exposure through "
        "logging, error messages, or child process inheritance."
    ),
    output_model=SecretsInEnvVarsOutput,
    facts=(_k8s_secrets_in_env_vars,),
    tags=("secrets", "environment-variables", "stride:information_disclosure"),
    version="1.0.0",
    references=CIS_REFERENCES,
    frameworks=(
        cis_kubernetes("5.4.1"),
        iso27001_annex_a("8.12"),
    ),
)


# =============================================================================
# CIS K8s 5.1.6: Service Account Tokens are only mounted where necessary
# Main node: KubernetesPod
# =============================================================================
class ServiceAccountTokenMountOutput(Finding):
    pod_id: str | None = None
    pod_name: str | None = None
    namespace: str | None = None
    service_account_name: str | None = None
    pod_automount_service_account_token: bool | None = None
    service_account_automount_service_account_token: bool | None = None
    cluster_name: str | None = None


_k8s_service_account_tokens_mounted = Fact(
    id="k8s_service_account_tokens_mounted",
    name="Kubernetes pods with service account token auto-mount enabled",
    description=(
        "Detects pods where service account tokens are still mounted by default or "
        "explicitly enabled. This is a heuristic for identifying workloads that may "
        "not need API credentials."
    ),
    cypher_query="""
    MATCH (cluster:KubernetesCluster)-[:RESOURCE]->(pod:KubernetesPod)
    OPTIONAL MATCH (pod)-[:USES_SERVICE_ACCOUNT]->(sa:KubernetesServiceAccount)
    WITH cluster, pod, sa, coalesce(pod.automount_service_account_token, sa.automount_service_account_token, true) AS effective_automount
    WHERE effective_automount = true
    AND NOT pod.namespace IN ['kube-system', 'kube-public', 'kube-node-lease']
    RETURN
        pod.id AS pod_id,
        pod.name AS pod_name,
        pod.namespace AS namespace,
        pod.service_account_name AS service_account_name,
        pod.automount_service_account_token AS pod_automount_service_account_token,
        sa.automount_service_account_token AS service_account_automount_service_account_token,
        cluster.name AS cluster_name
    """,
    cypher_visual_query="""
    MATCH p=(cluster:KubernetesCluster)-[:RESOURCE]->(pod:KubernetesPod)
    OPTIONAL MATCH p1=(pod)-[:USES_SERVICE_ACCOUNT]->(sa:KubernetesServiceAccount)
    WITH cluster, pod, sa, p, p1, coalesce(pod.automount_service_account_token, sa.automount_service_account_token, true) AS effective_automount
    WHERE effective_automount = true
    AND NOT pod.namespace IN ['kube-system', 'kube-public', 'kube-node-lease']
    RETURN *
    """,
    cypher_count_query="""
    MATCH (pod:KubernetesPod)
    WHERE NOT pod.namespace IN ['kube-system', 'kube-public', 'kube-node-lease']
    RETURN COUNT(pod) AS count
    """,
    asset_id_field="pod_id",
    module=Module.KUBERNETES,
    maturity=Maturity.EXPERIMENTAL,
)

cis_k8s_5_1_6_sa_token_mounts = Rule(
    id="cis_k8s_5_1_6_sa_token_mounts",
    name="CIS K8s 5.1.6: Service Account Tokens Mounted in Pods",
    description=(
        "Service account tokens should only be mounted into pods that explicitly need "
        "to communicate with the Kubernetes API."
    ),
    output_model=ServiceAccountTokenMountOutput,
    facts=(_k8s_service_account_tokens_mounted,),
    tags=("service-accounts", "tokens", "workloads", "stride:elevation_of_privilege"),
    version="1.0.0",
    references=CIS_REFERENCES,
    frameworks=(
        cis_kubernetes("5.1.6"),
        iso27001_annex_a("5.17"),
    ),
)


# =============================================================================
# TODO: CIS K8s 5.1.6: Partial control coverage
# Missing datamodel or evidence: proof of whether a workload actually needs Kubernetes API access; current rule can only detect token mounts, not necessity
# =============================================================================


# =============================================================================
# CIS K8s 5.2.3: Minimize admission of containers sharing host PID namespace
# Main node: KubernetesPod
# =============================================================================
class HostPidOutput(Finding):
    pod_id: str | None = None
    pod_name: str | None = None
    namespace: str | None = None
    cluster_name: str | None = None


_k8s_host_pid_pods = Fact(
    id="k8s_host_pid_pods",
    name="Kubernetes pods sharing the host PID namespace",
    description="Detects pods configured with hostPID=true.",
    cypher_query="""
    MATCH (cluster:KubernetesCluster)-[:RESOURCE]->(pod:KubernetesPod)
    WHERE coalesce(pod.host_pid, false) = true
    RETURN pod.id AS pod_id, pod.name AS pod_name, pod.namespace AS namespace, cluster.name AS cluster_name
    """,
    cypher_visual_query="""
    MATCH p=(cluster:KubernetesCluster)-[:RESOURCE]->(pod:KubernetesPod)
    WHERE coalesce(pod.host_pid, false) = true
    RETURN *
    """,
    cypher_count_query="""
    MATCH (pod:KubernetesPod)
    RETURN COUNT(pod) AS count
    """,
    asset_id_field="pod_id",
    module=Module.KUBERNETES,
    maturity=Maturity.EXPERIMENTAL,
)

cis_k8s_5_2_3_host_pid = Rule(
    id="cis_k8s_5_2_3_host_pid",
    name="CIS K8s 5.2.3: Pods Sharing Host PID Namespace",
    description="Pods should not generally share the host PID namespace.",
    output_model=HostPidOutput,
    facts=(_k8s_host_pid_pods,),
    tags=("pod-security", "hostpid", "stride:elevation_of_privilege"),
    version="1.0.0",
    references=CIS_REFERENCES,
    frameworks=(
        cis_kubernetes("5.2.3"),
        iso27001_annex_a("8.9"),
    ),
)


# =============================================================================
# CIS K8s 5.2.4: Minimize admission of containers sharing host IPC namespace
# Main node: KubernetesPod
# =============================================================================
class HostIpcOutput(Finding):
    pod_id: str | None = None
    pod_name: str | None = None
    namespace: str | None = None
    cluster_name: str | None = None


_k8s_host_ipc_pods = Fact(
    id="k8s_host_ipc_pods",
    name="Kubernetes pods sharing the host IPC namespace",
    description="Detects pods configured with hostIPC=true.",
    cypher_query="""
    MATCH (cluster:KubernetesCluster)-[:RESOURCE]->(pod:KubernetesPod)
    WHERE coalesce(pod.host_ipc, false) = true
    RETURN pod.id AS pod_id, pod.name AS pod_name, pod.namespace AS namespace, cluster.name AS cluster_name
    """,
    cypher_visual_query="""
    MATCH p=(cluster:KubernetesCluster)-[:RESOURCE]->(pod:KubernetesPod)
    WHERE coalesce(pod.host_ipc, false) = true
    RETURN *
    """,
    cypher_count_query="""
    MATCH (pod:KubernetesPod)
    RETURN COUNT(pod) AS count
    """,
    asset_id_field="pod_id",
    module=Module.KUBERNETES,
    maturity=Maturity.EXPERIMENTAL,
)

cis_k8s_5_2_4_host_ipc = Rule(
    id="cis_k8s_5_2_4_host_ipc",
    name="CIS K8s 5.2.4: Pods Sharing Host IPC Namespace",
    description="Pods should not generally share the host IPC namespace.",
    output_model=HostIpcOutput,
    facts=(_k8s_host_ipc_pods,),
    tags=("pod-security", "hostipc", "stride:elevation_of_privilege"),
    version="1.0.0",
    references=CIS_REFERENCES,
    frameworks=(
        cis_kubernetes("5.2.4"),
        iso27001_annex_a("8.9"),
    ),
)


# =============================================================================
# CIS K8s 5.2.5: Minimize admission of containers sharing host network namespace
# Main node: KubernetesPod
# =============================================================================
class HostNetworkOutput(Finding):
    pod_id: str | None = None
    pod_name: str | None = None
    namespace: str | None = None
    cluster_name: str | None = None


_k8s_host_network_pods = Fact(
    id="k8s_host_network_pods",
    name="Kubernetes pods sharing the host network namespace",
    description="Detects pods configured with hostNetwork=true.",
    cypher_query="""
    MATCH (cluster:KubernetesCluster)-[:RESOURCE]->(pod:KubernetesPod)
    WHERE coalesce(pod.host_network, false) = true
    RETURN pod.id AS pod_id, pod.name AS pod_name, pod.namespace AS namespace, cluster.name AS cluster_name
    """,
    cypher_visual_query="""
    MATCH p=(cluster:KubernetesCluster)-[:RESOURCE]->(pod:KubernetesPod)
    WHERE coalesce(pod.host_network, false) = true
    RETURN *
    """,
    cypher_count_query="""
    MATCH (pod:KubernetesPod)
    RETURN COUNT(pod) AS count
    """,
    asset_id_field="pod_id",
    module=Module.KUBERNETES,
    maturity=Maturity.EXPERIMENTAL,
)

cis_k8s_5_2_5_host_network = Rule(
    id="cis_k8s_5_2_5_host_network",
    name="CIS K8s 5.2.5: Pods Sharing Host Network Namespace",
    description="Pods should not generally share the host network namespace.",
    output_model=HostNetworkOutput,
    facts=(_k8s_host_network_pods,),
    tags=("pod-security", "hostnetwork", "stride:elevation_of_privilege"),
    version="1.0.0",
    references=CIS_REFERENCES,
    frameworks=(
        cis_kubernetes("5.2.5"),
        iso27001_annex_a("8.9"),
        iso27001_annex_a("8.20"),
    ),
)


# =============================================================================
# CIS K8s 5.2.6: Minimize admission of containers with allowPrivilegeEscalation
# Main node: KubernetesContainer
# =============================================================================
class AllowPrivilegeEscalationOutput(Finding):
    container_id: str | None = None
    container_name: str | None = None
    image: str | None = None
    namespace: str | None = None
    cluster_name: str | None = None


_k8s_allow_privilege_escalation = Fact(
    id="k8s_allow_privilege_escalation",
    name="Kubernetes containers without allowPrivilegeEscalation explicitly set to false",
    description=(
        "Detects containers whose allowPrivilegeEscalation is not explicitly set to false. "
        "The CIS restricted profile requires this field to be false; containers that omit "
        "the field also fail the control."
    ),
    cypher_query="""
    MATCH (cluster:KubernetesCluster)-[:RESOURCE]->(c:KubernetesContainer)
    WHERE coalesce(c.allow_privilege_escalation, true) = true
    RETURN c.id AS container_id, c.name AS container_name, c.image AS image, c.namespace AS namespace, cluster.name AS cluster_name
    """,
    cypher_visual_query="""
    MATCH p=(cluster:KubernetesCluster)-[:RESOURCE]->(c:KubernetesContainer)
    WHERE coalesce(c.allow_privilege_escalation, true) = true
    RETURN *
    """,
    cypher_count_query="""
    MATCH (c:KubernetesContainer)
    RETURN COUNT(c) AS count
    """,
    asset_id_field="container_id",
    module=Module.KUBERNETES,
    maturity=Maturity.EXPERIMENTAL,
)

cis_k8s_5_2_6_allow_privilege_escalation = Rule(
    id="cis_k8s_5_2_6_allow_privilege_escalation",
    name="CIS K8s 5.2.6: Containers Allowing Privilege Escalation",
    description="Containers should not generally allow privilege escalation.",
    output_model=AllowPrivilegeEscalationOutput,
    facts=(_k8s_allow_privilege_escalation,),
    tags=("pod-security", "privilege-escalation", "stride:elevation_of_privilege"),
    version="1.0.0",
    references=CIS_REFERENCES,
    frameworks=(
        cis_kubernetes("5.2.6"),
        iso27001_annex_a("8.9"),
    ),
)

# =============================================================================
# TODO: CIS K8s 5.2.6: Partial control coverage
# Missing datamodel or evidence: initContainers and ephemeralContainers securityContext fields; current rule evaluates regular containers only
# =============================================================================


# =============================================================================
# CIS K8s 5.2.11: Minimize admission of HostPath volumes
# Main node: KubernetesPod
# =============================================================================
class HostPathVolumeOutput(Finding):
    pod_id: str | None = None
    pod_name: str | None = None
    namespace: str | None = None
    host_path_volume_paths: list[str] | None = None
    cluster_name: str | None = None


_k8s_host_path_volumes = Fact(
    id="k8s_host_path_volumes",
    name="Kubernetes pods using hostPath volumes",
    description="Detects pods that define one or more hostPath volumes.",
    cypher_query="""
    MATCH (cluster:KubernetesCluster)-[:RESOURCE]->(pod:KubernetesPod)
    WHERE size(coalesce(pod.host_path_volume_paths, [])) > 0
    RETURN
        pod.id AS pod_id,
        pod.name AS pod_name,
        pod.namespace AS namespace,
        pod.host_path_volume_paths AS host_path_volume_paths,
        cluster.name AS cluster_name
    """,
    cypher_visual_query="""
    MATCH p=(cluster:KubernetesCluster)-[:RESOURCE]->(pod:KubernetesPod)
    WHERE size(coalesce(pod.host_path_volume_paths, [])) > 0
    RETURN *
    """,
    cypher_count_query="""
    MATCH (pod:KubernetesPod)
    RETURN COUNT(pod) AS count
    """,
    asset_id_field="pod_id",
    module=Module.KUBERNETES,
    maturity=Maturity.EXPERIMENTAL,
)

cis_k8s_5_2_11_host_path_volumes = Rule(
    id="cis_k8s_5_2_11_host_path_volumes",
    name="CIS K8s 5.2.11: Pods Using HostPath Volumes",
    description="Pods should not generally use hostPath volumes because they expose the host filesystem.",
    output_model=HostPathVolumeOutput,
    facts=(_k8s_host_path_volumes,),
    tags=("pod-security", "hostpath", "stride:elevation_of_privilege"),
    version="1.0.0",
    references=CIS_REFERENCES,
    frameworks=(
        cis_kubernetes("5.2.11"),
        iso27001_annex_a("8.9"),
    ),
)


# =============================================================================
# CIS K8s 5.2.12: Minimize admission of containers which use HostPorts
# Main node: KubernetesContainer
# =============================================================================
class HostPortOutput(Finding):
    container_id: str | None = None
    container_name: str | None = None
    namespace: str | None = None
    host_ports: list[int] | None = None
    cluster_name: str | None = None


_k8s_host_ports = Fact(
    id="k8s_host_ports",
    name="Kubernetes containers using host ports",
    description="Detects containers that expose one or more hostPort values.",
    cypher_query="""
    MATCH (cluster:KubernetesCluster)-[:RESOURCE]->(c:KubernetesContainer)
    WHERE size(coalesce(c.host_ports, [])) > 0
    RETURN c.id AS container_id, c.name AS container_name, c.namespace AS namespace, c.host_ports AS host_ports, cluster.name AS cluster_name
    """,
    cypher_visual_query="""
    MATCH p=(cluster:KubernetesCluster)-[:RESOURCE]->(c:KubernetesContainer)
    WHERE size(coalesce(c.host_ports, [])) > 0
    RETURN *
    """,
    cypher_count_query="""
    MATCH (c:KubernetesContainer)
    RETURN COUNT(c) AS count
    """,
    asset_id_field="container_id",
    module=Module.KUBERNETES,
    maturity=Maturity.EXPERIMENTAL,
)

cis_k8s_5_2_12_host_ports = Rule(
    id="cis_k8s_5_2_12_host_ports",
    name="CIS K8s 5.2.12: Containers Using HostPorts",
    description="Containers should not generally use hostPorts because they bypass normal cluster networking controls.",
    output_model=HostPortOutput,
    facts=(_k8s_host_ports,),
    tags=("pod-security", "hostports", "networking", "stride:elevation_of_privilege"),
    version="1.0.0",
    references=CIS_REFERENCES,
    frameworks=(
        cis_kubernetes("5.2.12"),
        iso27001_annex_a("8.9"),
        iso27001_annex_a("8.20"),
    ),
)

# =============================================================================
# TODO: CIS K8s 5.2.12: Partial control coverage
# Missing datamodel or evidence: initContainers and ephemeralContainers port definitions; current rule evaluates regular containers only
# =============================================================================


# =============================================================================
# CIS K8s 5.6.2: seccomp profile is set to RuntimeDefault in pod definitions
# Main node: KubernetesPod
# =============================================================================
class SeccompRuntimeDefaultOutput(Finding):
    pod_id: str | None = None
    pod_name: str | None = None
    namespace: str | None = None
    pod_seccomp_profile_type: str | None = None
    container_names_without_runtime_default: list[str] | None = None
    cluster_name: str | None = None


_k8s_missing_runtime_default_seccomp = Fact(
    id="k8s_missing_runtime_default_seccomp",
    name="Kubernetes pods without RuntimeDefault seccomp coverage",
    description=(
        "Detects pods where the effective seccomp profile is not RuntimeDefault for at "
        "least one container. A container's effective profile is its own seccompProfile "
        "if set, otherwise the pod-level seccompProfile. Container-level overrides such "
        "as Unconfined fail the control even when the pod sets RuntimeDefault."
    ),
    cypher_query="""
    MATCH (cluster:KubernetesCluster)-[:RESOURCE]->(pod:KubernetesPod)
    OPTIONAL MATCH (pod)<-[:CONTAINS]-(c:KubernetesContainer)
    WITH cluster, pod, collect(c) AS containers
    WITH
        cluster,
        pod,
        [container IN containers WHERE coalesce(container.seccomp_profile_type, pod.seccomp_profile_type, '') <> 'RuntimeDefault' | container.name] AS container_names_without_runtime_default
    WHERE size(container_names_without_runtime_default) > 0
    RETURN
        pod.id AS pod_id,
        pod.name AS pod_name,
        pod.namespace AS namespace,
        pod.seccomp_profile_type AS pod_seccomp_profile_type,
        container_names_without_runtime_default,
        cluster.name AS cluster_name
    """,
    cypher_visual_query="""
    MATCH p=(cluster:KubernetesCluster)-[:RESOURCE]->(pod:KubernetesPod)
    OPTIONAL MATCH p1=(pod)<-[:CONTAINS]-(c:KubernetesContainer)
    WITH cluster, pod, p, p1, collect(c) AS containers
    WITH cluster, pod, p, p1, [container IN containers WHERE coalesce(container.seccomp_profile_type, pod.seccomp_profile_type, '') <> 'RuntimeDefault' | container] AS non_runtime_default_containers
    WHERE size(non_runtime_default_containers) > 0
    RETURN *
    """,
    cypher_count_query="""
    MATCH (pod:KubernetesPod)
    RETURN COUNT(pod) AS count
    """,
    asset_id_field="pod_id",
    module=Module.KUBERNETES,
    maturity=Maturity.EXPERIMENTAL,
)

cis_k8s_5_6_2_runtime_default_seccomp = Rule(
    id="cis_k8s_5_6_2_runtime_default_seccomp",
    name="CIS K8s 5.6.2: Pods Missing RuntimeDefault Seccomp",
    description="Pods should set the RuntimeDefault seccomp profile at the pod or container level.",
    output_model=SeccompRuntimeDefaultOutput,
    facts=(_k8s_missing_runtime_default_seccomp,),
    tags=("pod-security", "seccomp", "runtime-default"),
    version="1.0.0",
    references=CIS_REFERENCES,
    frameworks=(
        cis_kubernetes("5.6.2"),
        iso27001_annex_a("8.9"),
    ),
)

# =============================================================================
# TODO: CIS K8s 5.6.2: Partial control coverage
# Missing datamodel or evidence: initContainers and ephemeralContainers seccompProfile settings; current rule evaluates the pod plus regular containers only
# =============================================================================


# =============================================================================
# CIS K8s 5.6.4: Default namespace should not be used
# Main node: KubernetesPod
# =============================================================================
class DefaultNamespaceOutput(Finding):
    """Output model for default namespace usage check."""

    pod_name: str | None = None
    status_phase: str | None = None
    cluster_name: str | None = None


_k8s_pods_in_default_namespace = Fact(
    id="k8s_pods_in_default_namespace",
    name="Kubernetes pods running in default namespace",
    description=(
        "Detects pods running in the default namespace. "
        "Resources should be segregated into namespaces to allow for "
        "resource quota management, network policy enforcement, and "
        "access control separation."
    ),
    cypher_query="""
    MATCH (cluster:KubernetesCluster)-[:RESOURCE]->(pod:KubernetesPod)
    WHERE pod.namespace = 'default'
    RETURN
        pod.name AS pod_name,
        pod.status_phase AS status_phase,
        cluster.name AS cluster_name
    """,
    cypher_visual_query="""
    MATCH p=(cluster:KubernetesCluster)-[:RESOURCE]->(pod:KubernetesPod)
    WHERE pod.namespace = 'default'
    RETURN *
    """,
    cypher_count_query="""
    MATCH (pod:KubernetesPod)
    RETURN COUNT(pod) AS count
    """,
    module=Module.KUBERNETES,
    maturity=Maturity.EXPERIMENTAL,
)

cis_k8s_5_6_4_default_namespace = Rule(
    id="cis_k8s_5_6_4_default_namespace",
    name="CIS K8s 5.6.4: Pods Running in Default Namespace",
    description=(
        "Kubernetes resources should not use the default namespace. "
        "Using dedicated namespaces allows for resource quota management, "
        "network policy enforcement, and access control separation. "
        "This rule checks for pods in the default namespace; other resource types "
        "(services, secrets, etc.) are not currently covered."
    ),
    output_model=DefaultNamespaceOutput,
    facts=(_k8s_pods_in_default_namespace,),
    tags=("namespaces", "general-policies", "stride:information_disclosure"),
    version="1.0.0",
    references=CIS_REFERENCES,
    frameworks=(cis_kubernetes("5.6.4"),),
)

# =============================================================================
# TODO: CIS K8s 5.6.4: Partial control coverage
# Missing datamodel: namespaced resource coverage beyond KubernetesPod; current rule does not inspect services, secrets, configmaps, jobs, or other namespaced objects in the default namespace
# =============================================================================

# =============================================================================
# TODO: CIS K8s 1.1.1: API server pod specification file permissions are set to 600 or more restrictive
# Missing datamodel: control plane host filesystem metadata for kube-apiserver manifest files
# =============================================================================

# =============================================================================
# TODO: CIS K8s 1.1.2: API server pod specification file ownership is set to root:root
# Missing datamodel: control plane host filesystem ownership metadata for kube-apiserver manifest files
# =============================================================================

# =============================================================================
# TODO: CIS K8s 1.1.3: Controller manager pod specification file permissions are set to 600 or more restrictive
# Missing datamodel: control plane host filesystem metadata for kube-controller-manager manifest files
# =============================================================================

# =============================================================================
# TODO: CIS K8s 1.1.4: Controller manager pod specification file ownership is set to root:root
# Missing datamodel: control plane host filesystem ownership metadata for kube-controller-manager manifest files
# =============================================================================

# =============================================================================
# TODO: CIS K8s 1.1.5: Scheduler pod specification file permissions are set to 600 or more restrictive
# Missing datamodel: control plane host filesystem metadata for kube-scheduler manifest files
# =============================================================================

# =============================================================================
# TODO: CIS K8s 1.1.6: Scheduler pod specification file ownership is set to root:root
# Missing datamodel: control plane host filesystem ownership metadata for kube-scheduler manifest files
# =============================================================================

# =============================================================================
# TODO: CIS K8s 1.1.7: etcd pod specification file permissions are set to 600 or more restrictive
# Missing datamodel: control plane host filesystem metadata for etcd manifest files
# =============================================================================

# =============================================================================
# TODO: CIS K8s 1.1.8: etcd pod specification file ownership is set to root:root
# Missing datamodel: control plane host filesystem ownership metadata for etcd manifest files
# =============================================================================

# =============================================================================
# TODO: CIS K8s 1.1.9: Container Network Interface file permissions are set to 600 or more restrictive
# Missing datamodel: host filesystem metadata for CNI configuration files and binaries
# =============================================================================

# =============================================================================
# TODO: CIS K8s 1.1.10: Container Network Interface file ownership is set to root:root
# Missing datamodel: host filesystem ownership metadata for CNI configuration files and binaries
# =============================================================================

# =============================================================================
# TODO: CIS K8s 1.1.11: etcd data directory permissions are set to 700 or more restrictive
# Missing datamodel: host filesystem metadata for the etcd data directory
# =============================================================================

# =============================================================================
# TODO: CIS K8s 1.1.12: etcd data directory ownership is set to etcd:etcd
# Missing datamodel: host filesystem ownership metadata for the etcd data directory
# =============================================================================

# =============================================================================
# TODO: CIS K8s 1.1.13: Default administrative credential file permissions are set to 600
# Missing datamodel: host filesystem metadata for admin.conf and super-admin.conf
# =============================================================================

# =============================================================================
# TODO: CIS K8s 1.1.14: Default administrative credential file ownership is set to root:root
# Missing datamodel: host filesystem ownership metadata for admin.conf and super-admin.conf
# =============================================================================

# =============================================================================
# TODO: CIS K8s 1.1.15: scheduler.conf file permissions are set to 600 or more restrictive
# Missing datamodel: host filesystem metadata for scheduler.conf
# =============================================================================

# =============================================================================
# TODO: CIS K8s 1.1.16: scheduler.conf file ownership is set to root:root
# Missing datamodel: host filesystem ownership metadata for scheduler.conf
# =============================================================================

# =============================================================================
# TODO: CIS K8s 1.1.17: controller-manager.conf file permissions are set to 600 or more restrictive
# Missing datamodel: host filesystem metadata for controller-manager.conf
# =============================================================================

# =============================================================================
# TODO: CIS K8s 1.1.18: controller-manager.conf file ownership is set to root:root
# Missing datamodel: host filesystem ownership metadata for controller-manager.conf
# =============================================================================

# =============================================================================
# TODO: CIS K8s 1.1.19: Kubernetes PKI directory and file ownership is set to root:root
# Missing datamodel: host filesystem ownership metadata for Kubernetes PKI directories and certificate material
# =============================================================================

# =============================================================================
# TODO: CIS K8s 1.1.20: Kubernetes PKI certificate file permissions are set to 644 or more restrictive
# Missing datamodel: host filesystem metadata for Kubernetes PKI certificate files
# =============================================================================

# =============================================================================
# TODO: CIS K8s 1.1.21: Kubernetes PKI key file permissions are set to 600
# Missing datamodel: host filesystem metadata for Kubernetes PKI key files
# =============================================================================

# =============================================================================
# TODO: CIS K8s 1.2.1: API server anonymous-auth is set to false
# Missing datamodel: kube-apiserver command arguments or parsed control plane configuration
# =============================================================================

# =============================================================================
# TODO: CIS K8s 1.2.2: token-auth-file parameter is not set
# Missing datamodel: kube-apiserver command arguments or parsed control plane configuration
# =============================================================================

# =============================================================================
# TODO: CIS K8s 1.2.3: DenyServiceExternalIPs admission controller is set
# Missing datamodel: kube-apiserver admission plugin configuration
# =============================================================================

# =============================================================================
# TODO: CIS K8s 1.2.4: kubelet-client-certificate and kubelet-client-key arguments are set as appropriate
# Missing datamodel: kube-apiserver command arguments for kubelet client TLS configuration
# =============================================================================

# =============================================================================
# TODO: CIS K8s 1.2.5: kubelet-certificate-authority argument is set as appropriate
# Missing datamodel: kube-apiserver command arguments for kubelet certificate authority configuration
# =============================================================================

# =============================================================================
# TODO: CIS K8s 1.2.6: authorization-mode argument is not set to AlwaysAllow
# Missing datamodel: kube-apiserver authorization-mode configuration
# =============================================================================

# =============================================================================
# TODO: CIS K8s 1.2.7: authorization-mode argument includes Node
# Missing datamodel: kube-apiserver authorization-mode configuration
# =============================================================================

# =============================================================================
# TODO: CIS K8s 1.2.8: authorization-mode argument includes RBAC
# Missing datamodel: kube-apiserver authorization-mode configuration
# =============================================================================

# =============================================================================
# TODO: CIS K8s 1.2.9: EventRateLimit admission controller is set
# Missing datamodel: kube-apiserver admission plugin and admission-control-config-file configuration
# =============================================================================

# =============================================================================
# TODO: CIS K8s 1.2.10: AlwaysAdmit admission controller is not set
# Missing datamodel: kube-apiserver admission plugin configuration
# =============================================================================

# =============================================================================
# TODO: CIS K8s 1.2.11: AlwaysPullImages admission controller is set
# Missing datamodel: kube-apiserver admission plugin configuration
# =============================================================================

# =============================================================================
# TODO: CIS K8s 1.2.12: ServiceAccount admission controller is set
# Missing datamodel: kube-apiserver disabled-admission-plugins configuration
# =============================================================================

# =============================================================================
# TODO: CIS K8s 1.2.13: NamespaceLifecycle admission controller is set
# Missing datamodel: kube-apiserver disabled-admission-plugins configuration
# =============================================================================

# =============================================================================
# TODO: CIS K8s 1.2.14: NodeRestriction admission controller is set
# Missing datamodel: kube-apiserver admission plugin configuration
# =============================================================================

# =============================================================================
# TODO: CIS K8s 1.2.15: API server profiling argument is set to false
# Missing datamodel: kube-apiserver command arguments or parsed control plane configuration
# =============================================================================

# =============================================================================
# TODO: CIS K8s 1.2.16: audit-log-path argument is set
# Missing datamodel: kube-apiserver command arguments for audit logging configuration
# =============================================================================

# =============================================================================
# TODO: CIS K8s 1.2.17: audit-log-maxage argument is set to 30 or as appropriate
# Missing datamodel: kube-apiserver command arguments for audit log retention
# =============================================================================

# =============================================================================
# TODO: CIS K8s 1.2.18: audit-log-maxbackup argument is set to 10 or as appropriate
# Missing datamodel: kube-apiserver command arguments for audit log backup retention
# =============================================================================

# =============================================================================
# TODO: CIS K8s 1.2.19: audit-log-maxsize argument is set to 100 or as appropriate
# Missing datamodel: kube-apiserver command arguments for audit log rotation size
# =============================================================================

# =============================================================================
# TODO: CIS K8s 1.2.20: request-timeout argument is set as appropriate
# Missing datamodel: kube-apiserver request-timeout configuration and environment-specific policy baseline
# =============================================================================

# =============================================================================
# TODO: CIS K8s 1.2.21: service-account-lookup argument is set to true
# Missing datamodel: kube-apiserver service account token validation configuration
# =============================================================================

# =============================================================================
# TODO: CIS K8s 1.2.22: service-account-key-file argument is set as appropriate
# Missing datamodel: kube-apiserver service account signing key configuration
# =============================================================================

# =============================================================================
# TODO: CIS K8s 1.2.23: etcd-certfile and etcd-keyfile arguments are set as appropriate
# Missing datamodel: kube-apiserver etcd TLS client configuration
# =============================================================================

# =============================================================================
# TODO: CIS K8s 1.2.24: tls-cert-file and tls-private-key-file arguments are set as appropriate
# Missing datamodel: kube-apiserver TLS serving certificate configuration
# =============================================================================

# =============================================================================
# TODO: CIS K8s 1.2.25: client-ca-file argument is set as appropriate
# Missing datamodel: kube-apiserver client certificate authority configuration
# =============================================================================

# =============================================================================
# TODO: CIS K8s 1.2.26: etcd-cafile argument is set as appropriate
# Missing datamodel: kube-apiserver etcd certificate authority configuration
# =============================================================================

# =============================================================================
# TODO: CIS K8s 1.2.27: encryption-provider-config argument is set as appropriate
# Missing datamodel: kube-apiserver encryption-provider-config path and parsed encryption configuration
# =============================================================================

# =============================================================================
# TODO: CIS K8s 1.2.28: Encryption providers are appropriately configured
# Missing datamodel: parsed encryption-provider configuration content for etcd resource coverage and provider selection
# =============================================================================

# =============================================================================
# TODO: CIS K8s 1.2.29: API server only makes use of strong cryptographic ciphers
# Missing datamodel: kube-apiserver tls-cipher-suites configuration
# =============================================================================

# =============================================================================
# TODO: CIS K8s 1.2.30: service-account-extend-token-expiration is set to false
# Missing datamodel: kube-apiserver service account token lifetime configuration
# =============================================================================

# =============================================================================
# TODO: CIS K8s 1.3.1: terminated-pod-gc-threshold argument is set as appropriate
# Missing datamodel: kube-controller-manager command arguments and environment-specific baseline for an appropriate threshold
# =============================================================================

# =============================================================================
# TODO: CIS K8s 1.3.2: Controller manager profiling argument is set to false
# Missing datamodel: kube-controller-manager command arguments
# =============================================================================

# =============================================================================
# TODO: CIS K8s 1.3.3: use-service-account-credentials argument is set to true
# Missing datamodel: kube-controller-manager command arguments
# =============================================================================

# =============================================================================
# TODO: CIS K8s 1.3.4: service-account-private-key-file argument is set as appropriate
# Missing datamodel: kube-controller-manager service account signing key configuration
# =============================================================================

# =============================================================================
# TODO: CIS K8s 1.3.5: root-ca-file argument is set as appropriate
# Missing datamodel: kube-controller-manager root CA configuration
# =============================================================================

# =============================================================================
# TODO: CIS K8s 1.3.6: RotateKubeletServerCertificate argument is set to true
# Missing datamodel: kube-controller-manager feature-gates configuration
# =============================================================================

# =============================================================================
# TODO: CIS K8s 1.3.7: Controller manager bind-address argument is set to 127.0.0.1
# Missing datamodel: kube-controller-manager bind-address configuration
# =============================================================================

# =============================================================================
# TODO: CIS K8s 1.4.1: Scheduler profiling argument is set to false
# Missing datamodel: kube-scheduler command arguments
# =============================================================================

# =============================================================================
# TODO: CIS K8s 1.4.2: Scheduler bind-address argument is set to 127.0.0.1
# Missing datamodel: kube-scheduler bind-address configuration
# =============================================================================

# =============================================================================
# TODO: CIS K8s 2.1: etcd cert-file and key-file arguments are set as appropriate
# Missing datamodel: etcd process arguments or parsed etcd configuration
# =============================================================================

# =============================================================================
# TODO: CIS K8s 2.2: etcd client-cert-auth argument is set to true
# Missing datamodel: etcd process arguments or parsed etcd configuration
# =============================================================================

# =============================================================================
# TODO: CIS K8s 2.3: etcd auto-tls argument is not set to true
# Missing datamodel: etcd process arguments or parsed etcd configuration
# =============================================================================

# =============================================================================
# TODO: CIS K8s 2.4: etcd peer-cert-file and peer-key-file arguments are set as appropriate
# Missing datamodel: etcd peer TLS configuration and cluster topology details
# =============================================================================

# =============================================================================
# TODO: CIS K8s 2.5: etcd peer-client-cert-auth argument is set to true
# Missing datamodel: etcd peer authentication configuration
# =============================================================================

# =============================================================================
# TODO: CIS K8s 2.6: etcd peer-auto-tls argument is not set to true
# Missing datamodel: etcd peer TLS configuration
# =============================================================================

# =============================================================================
# TODO: CIS K8s 2.7: A unique Certificate Authority is used for etcd
# Missing datamodel: etcd trusted CA configuration and comparable API server client CA material
# =============================================================================

# =============================================================================
# TODO: CIS K8s 3.1.1: Client certificate authentication should not be used for users
# Missing datamodel: user authentication method provenance linking KubernetesUser identities to client-certificate auth versus OIDC or other mechanisms
# =============================================================================

# =============================================================================
# TODO: CIS K8s 3.1.2: Service account token authentication should not be used for users
# Missing datamodel: user authentication method provenance linking human users to service account token usage
# =============================================================================

# =============================================================================
# TODO: CIS K8s 3.1.3: Bootstrap token authentication should not be used for users
# Missing datamodel: bootstrap token inventory and linkage between human users and bootstrap-token authentication
# =============================================================================

# =============================================================================
# TODO: CIS K8s 3.2.1: A minimal audit policy is created
# Missing datamodel: audit policy file inventory and parsed audit policy content
# =============================================================================

# =============================================================================
# TODO: CIS K8s 3.2.2: Audit policy covers key security concerns
# Missing datamodel: parsed audit policy content for resource and verb coverage
# =============================================================================

# =============================================================================
# TODO: CIS K8s 4.1.1: kubelet service file permissions are set to 600 or more restrictive
# Missing datamodel: worker-node host filesystem metadata for kubelet service files
# =============================================================================

# =============================================================================
# TODO: CIS K8s 4.1.2: kubelet service file ownership is set to root:root
# Missing datamodel: worker-node host filesystem ownership metadata for kubelet service files
# =============================================================================

# =============================================================================
# TODO: CIS K8s 4.1.3: proxy kubeconfig file permissions are set to 600 or more restrictive
# Missing datamodel: worker-node host filesystem metadata for kube-proxy kubeconfig files
# =============================================================================

# =============================================================================
# TODO: CIS K8s 4.1.4: proxy kubeconfig file ownership is set to root:root
# Missing datamodel: worker-node host filesystem ownership metadata for kube-proxy kubeconfig files
# =============================================================================

# =============================================================================
# TODO: CIS K8s 4.1.5: kubelet.conf file permissions are set to 600 or more restrictive
# Missing datamodel: worker-node host filesystem metadata for kubelet.conf
# =============================================================================

# =============================================================================
# TODO: CIS K8s 4.1.6: kubelet.conf file ownership is set to root:root
# Missing datamodel: worker-node host filesystem ownership metadata for kubelet.conf
# =============================================================================

# =============================================================================
# TODO: CIS K8s 4.1.7: Certificate authorities file permissions are set to 644 or more restrictive
# Missing datamodel: worker-node host filesystem metadata for kubelet client CA files
# =============================================================================

# =============================================================================
# TODO: CIS K8s 4.1.8: Client certificate authorities file ownership is set to root:root
# Missing datamodel: worker-node host filesystem ownership metadata for kubelet client CA files
# =============================================================================

# =============================================================================
# TODO: CIS K8s 4.1.9: kubelet config.yaml permissions are set to 600 or more restrictive
# Missing datamodel: worker-node host filesystem metadata for kubelet config files
# =============================================================================

# =============================================================================
# TODO: CIS K8s 4.1.10: kubelet config.yaml file ownership is set to root:root
# Missing datamodel: worker-node host filesystem ownership metadata for kubelet config files
# =============================================================================

# =============================================================================
# TODO: CIS K8s 4.2.1: kubelet anonymous-auth is set to false
# Missing datamodel: kubelet command arguments or parsed kubelet configuration
# =============================================================================

# =============================================================================
# TODO: CIS K8s 4.2.2: kubelet authorization-mode is not set to AlwaysAllow
# Missing datamodel: kubelet command arguments or parsed kubelet configuration
# =============================================================================

# =============================================================================
# TODO: CIS K8s 4.2.3: kubelet client-ca-file is set as appropriate
# Missing datamodel: kubelet client certificate authority configuration
# =============================================================================

# =============================================================================
# TODO: CIS K8s 4.2.4: readOnlyPort is set to 0 if defined
# Missing datamodel: kubelet readOnlyPort configuration
# =============================================================================

# =============================================================================
# TODO: CIS K8s 4.2.5: streaming-connection-idle-timeout is not set to 0
# Missing datamodel: kubelet streamingConnectionIdleTimeout configuration
# =============================================================================

# =============================================================================
# TODO: CIS K8s 4.2.6: make-iptables-util-chains is set to true
# Missing datamodel: kubelet makeIPTablesUtilChains configuration
# =============================================================================

# =============================================================================
# TODO: CIS K8s 4.2.7: hostname-override argument is not set
# Missing datamodel: kubelet hostname-override command argument
# =============================================================================

# =============================================================================
# TODO: CIS K8s 4.2.8: eventRecordQPS is set to an appropriate level
# Missing datamodel: kubelet eventRecordQPS configuration and environment-specific baseline for an appropriate value
# =============================================================================

# =============================================================================
# TODO: CIS K8s 4.2.9: kubelet tls-cert-file and tls-private-key-file are set as appropriate
# Missing datamodel: kubelet TLS serving certificate configuration
# =============================================================================

# =============================================================================
# TODO: CIS K8s 4.2.10: rotate-certificates is not set to false
# Missing datamodel: kubelet rotateCertificates configuration
# =============================================================================

# =============================================================================
# TODO: CIS K8s 4.2.11: RotateKubeletServerCertificate argument is set to true
# Missing datamodel: kubelet feature-gates or serverTLSBootstrap configuration
# =============================================================================

# =============================================================================
# TODO: CIS K8s 4.2.12: Kubelet only makes use of strong cryptographic ciphers
# Missing datamodel: kubelet tlsCipherSuites configuration
# =============================================================================

# =============================================================================
# TODO: CIS K8s 4.2.13: A limit is set on pod PIDs
# Missing datamodel: kubelet podPidsLimit configuration
# =============================================================================

# =============================================================================
# TODO: CIS K8s 4.2.14: seccomp-default parameter is set to true
# Missing datamodel: kubelet seccompDefault configuration
# =============================================================================

# =============================================================================
# TODO: CIS K8s 4.3.1: kube-proxy metrics service is bound to localhost
# Missing datamodel: kube-proxy metricsBindAddress configuration or parsed kube-proxy config file
# =============================================================================

# =============================================================================
# TODO: CIS K8s 5.2.1: Cluster has at least one active policy control mechanism in place
# Missing datamodel: Pod Security Admission configuration, admission webhook policy inventory, or namespace-level policy enforcement labels
# =============================================================================

# =============================================================================
# TODO: CIS K8s 5.2.2: Minimize the admission of privileged containers
# Missing datamodel: pod or container securityContext.privileged and admission policy configuration
# =============================================================================

# =============================================================================
# TODO: CIS K8s 5.2.7: Minimize the admission of root containers
# Missing datamodel: pod and container runAsUser, runAsNonRoot, and related securityContext fields, plus admission policy configuration
# =============================================================================

# =============================================================================
# TODO: CIS K8s 5.2.8: Minimize the admission of containers with the NET_RAW capability
# Missing datamodel: container securityContext capabilities and admission policy configuration
# =============================================================================

# =============================================================================
# TODO: CIS K8s 5.2.9: Minimize the admission of containers with capabilities assigned
# Missing datamodel: container securityContext capabilities and admission policy configuration
# =============================================================================

# =============================================================================
# TODO: CIS K8s 5.2.10: Minimize the admission of Windows HostProcess Containers
# Missing datamodel: Windows securityContext.windowsOptions.hostProcess and admission policy configuration
# =============================================================================

# =============================================================================
# TODO: CIS K8s 5.3.1: CNI in use supports Network Policies
# Missing datamodel: CNI plugin inventory and capability metadata for ingress and egress NetworkPolicy support
# =============================================================================

# =============================================================================
# TODO: CIS K8s 5.3.2: All Namespaces have Network Policies defined
# Missing datamodel: KubernetesNetworkPolicy objects and namespace-to-policy relationships
# =============================================================================

# =============================================================================
# TODO: CIS K8s 5.4.2: Consider external secret storage
# Missing datamodel: external secret provider inventory, authentication model, audit capability, and secret-store integration metadata
# =============================================================================

# =============================================================================
# TODO: CIS K8s 5.5.1: Configure Image Provenance using ImagePolicyWebhook admission controller
# Missing datamodel: ImagePolicyWebhook admission configuration and image provenance policy metadata
# =============================================================================

# =============================================================================
# TODO: CIS K8s 5.6.1: Create administrative boundaries between resources using namespaces
# Missing datamodel: namespace-to-principal administrative boundary evidence; current graph inventories namespaces but not whether access boundaries are appropriately enforced between them
# =============================================================================

# =============================================================================
# TODO: CIS K8s 5.6.3: Apply Security Context to Pods and Containers
# Missing datamodel: pod, container, and volume securityContext fields beyond the limited pod and container properties currently ingested
# =============================================================================
