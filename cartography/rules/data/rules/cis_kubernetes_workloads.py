"""
CIS Kubernetes Workload and General Policy Security Checks

Implements CIS Kubernetes Benchmark Sections 5.4 and 5.6
Based on CIS Kubernetes Benchmark v1.12.0

Section 5.4: Secrets Management
Section 5.6: General Policies
"""

from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Framework
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
    namespace: str | None = None
    secret_name: str | None = None
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
        pod.name AS pod_name,
        pod.namespace AS namespace,
        secret.name AS secret_name,
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
    asset_id_field="pod_name",
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
        Framework(
            name="CIS Kubernetes Benchmark",
            short_name="CIS",
            scope="kubernetes",
            revision="1.12",
            requirement="5.4.1",
        ),
    ),
)


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
    name="CIS K8s 5.6.4: Default Namespace Usage",
    description=(
        "Kubernetes resources should not use the default namespace. "
        "Using dedicated namespaces allows for resource quota management, "
        "network policy enforcement, and access control separation."
    ),
    output_model=DefaultNamespaceOutput,
    facts=(_k8s_pods_in_default_namespace,),
    tags=("namespaces", "general-policies", "stride:information_disclosure"),
    version="1.0.0",
    references=CIS_REFERENCES,
    frameworks=(
        Framework(
            name="CIS Kubernetes Benchmark",
            short_name="CIS",
            scope="kubernetes",
            revision="1.12",
            requirement="5.6.4",
        ),
    ),
)
