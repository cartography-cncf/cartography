from cartography.rules.data.frameworks.iso27001 import iso27001_annex_a
from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule

_k8s_privileged_workloads_with_aws_identity = Fact(
    id="k8s_privileged_workloads_with_aws_identity",
    name="Privileged Kubernetes workloads bound to AWS roles",
    description=(
        "Kubernetes pods with host/privilege indicators whose service account "
        "can assume an AWS IAM role."
    ),
    cypher_query="""
    MATCH (cluster:KubernetesCluster)-[:RESOURCE]->(pod:KubernetesPod)
          -[:USES_SERVICE_ACCOUNT]->(sa:KubernetesServiceAccount)
          -[:ASSUMES_ROLE]->(role:AWSRole)
    WHERE NOT pod.namespace IN ['kube-system', 'kube-public', 'kube-node-lease']
    OPTIONAL MATCH (container:KubernetesContainer)-[:WORKLOAD_PARENT]->(pod)
    WITH cluster, pod, sa, role, collect(container) AS containers
    WITH cluster, pod, sa, role,
         [reason IN [
             CASE WHEN coalesce(pod.host_pid, false) THEN 'host_pid' ELSE null END,
             CASE WHEN coalesce(pod.host_ipc, false) THEN 'host_ipc' ELSE null END,
             CASE WHEN coalesce(pod.host_network, false) THEN 'host_network' ELSE null END,
             CASE WHEN size(coalesce(pod.host_path_volume_paths, [])) > 0 THEN 'host_path_volume' ELSE null END
         ] WHERE reason IS NOT NULL]
         + reduce(container_reasons = [], c IN containers |
             container_reasons + [reason IN [
                 CASE WHEN coalesce(c.allow_privilege_escalation, false) THEN 'allow_privilege_escalation' ELSE null END,
                 CASE WHEN 'SYS_ADMIN' IN coalesce(c.added_capabilities, []) THEN 'cap_sys_admin' ELSE null END,
                 CASE WHEN 'NET_ADMIN' IN coalesce(c.added_capabilities, []) THEN 'cap_net_admin' ELSE null END,
                 CASE WHEN size(coalesce(c.host_ports, [])) > 0 THEN 'host_ports' ELSE null END
             ] WHERE reason IS NOT NULL]
         ) AS privilege_reasons
    WHERE size(privilege_reasons) > 0
    RETURN DISTINCT
        pod.id AS pod_id,
        pod.name AS pod_name,
        pod.namespace AS namespace,
        cluster.name AS cluster_name,
        sa.name AS service_account,
        role.arn AS cloud_identity,
        'aws' AS cloud_provider,
        privilege_reasons
    ORDER BY cluster_name, namespace, pod_name, cloud_identity
    """,
    cypher_visual_query="""
    MATCH p=(cluster:KubernetesCluster)-[:RESOURCE]->(pod:KubernetesPod)
          -[:USES_SERVICE_ACCOUNT]->(sa:KubernetesServiceAccount)
          -[:ASSUMES_ROLE]->(role:AWSRole)
    WHERE NOT pod.namespace IN ['kube-system', 'kube-public', 'kube-node-lease']
      AND (
       coalesce(pod.host_pid, false)
       OR coalesce(pod.host_ipc, false)
       OR coalesce(pod.host_network, false)
       OR size(coalesce(pod.host_path_volume_paths, [])) > 0
       OR EXISTS {
           MATCH (container:KubernetesContainer)-[:WORKLOAD_PARENT]->(pod)
           WHERE coalesce(container.allow_privilege_escalation, false)
              OR 'SYS_ADMIN' IN coalesce(container.added_capabilities, [])
              OR 'NET_ADMIN' IN coalesce(container.added_capabilities, [])
              OR size(coalesce(container.host_ports, [])) > 0
       }
      )
    OPTIONAL MATCH p2=(container:KubernetesContainer)-[:WORKLOAD_PARENT]->(pod)
    RETURN *
    """,
    cypher_count_query="""
    MATCH (pod:KubernetesPod)-[:USES_SERVICE_ACCOUNT]->(:KubernetesServiceAccount)
          -[:ASSUMES_ROLE]->(:AWSRole)
    WHERE NOT pod.namespace IN ['kube-system', 'kube-public', 'kube-node-lease']
    RETURN COUNT(DISTINCT pod) AS count
    """,
    asset_id_field="pod_id",
    module=Module.KUBERNETES,
    maturity=Maturity.EXPERIMENTAL,
)

_k8s_privileged_workloads_with_gcp_identity = Fact(
    id="k8s_privileged_workloads_with_gcp_identity",
    name="Privileged Kubernetes workloads bound to GCP service accounts",
    description=(
        "Kubernetes pods with host/privilege indicators whose service account "
        "can impersonate a GCP service account through Workload Identity."
    ),
    cypher_query="""
    MATCH (cluster:KubernetesCluster)-[:RESOURCE]->(pod:KubernetesPod)
          -[:USES_SERVICE_ACCOUNT]->(sa:KubernetesServiceAccount)
          -[:WORKLOAD_IDENTITY_BINDING]->(gsa:GCPServiceAccount)
    WHERE NOT pod.namespace IN ['kube-system', 'kube-public', 'kube-node-lease']
    OPTIONAL MATCH (container:KubernetesContainer)-[:WORKLOAD_PARENT]->(pod)
    WITH cluster, pod, sa, gsa, collect(container) AS containers
    WITH cluster, pod, sa, gsa,
         [reason IN [
             CASE WHEN coalesce(pod.host_pid, false) THEN 'host_pid' ELSE null END,
             CASE WHEN coalesce(pod.host_ipc, false) THEN 'host_ipc' ELSE null END,
             CASE WHEN coalesce(pod.host_network, false) THEN 'host_network' ELSE null END,
             CASE WHEN size(coalesce(pod.host_path_volume_paths, [])) > 0 THEN 'host_path_volume' ELSE null END
         ] WHERE reason IS NOT NULL]
         + reduce(container_reasons = [], c IN containers |
             container_reasons + [reason IN [
                 CASE WHEN coalesce(c.allow_privilege_escalation, false) THEN 'allow_privilege_escalation' ELSE null END,
                 CASE WHEN 'SYS_ADMIN' IN coalesce(c.added_capabilities, []) THEN 'cap_sys_admin' ELSE null END,
                 CASE WHEN 'NET_ADMIN' IN coalesce(c.added_capabilities, []) THEN 'cap_net_admin' ELSE null END,
                 CASE WHEN size(coalesce(c.host_ports, [])) > 0 THEN 'host_ports' ELSE null END
             ] WHERE reason IS NOT NULL]
         ) AS privilege_reasons
    WHERE size(privilege_reasons) > 0
    RETURN DISTINCT
        pod.id AS pod_id,
        pod.name AS pod_name,
        pod.namespace AS namespace,
        cluster.name AS cluster_name,
        sa.name AS service_account,
        coalesce(gsa.email, gsa.id) AS cloud_identity,
        'gcp' AS cloud_provider,
        privilege_reasons
    ORDER BY cluster_name, namespace, pod_name, cloud_identity
    """,
    cypher_visual_query="""
    MATCH p=(cluster:KubernetesCluster)-[:RESOURCE]->(pod:KubernetesPod)
          -[:USES_SERVICE_ACCOUNT]->(sa:KubernetesServiceAccount)
          -[:WORKLOAD_IDENTITY_BINDING]->(gsa:GCPServiceAccount)
    WHERE NOT pod.namespace IN ['kube-system', 'kube-public', 'kube-node-lease']
      AND (
       coalesce(pod.host_pid, false)
       OR coalesce(pod.host_ipc, false)
       OR coalesce(pod.host_network, false)
       OR size(coalesce(pod.host_path_volume_paths, [])) > 0
       OR EXISTS {
           MATCH (container:KubernetesContainer)-[:WORKLOAD_PARENT]->(pod)
           WHERE coalesce(container.allow_privilege_escalation, false)
              OR 'SYS_ADMIN' IN coalesce(container.added_capabilities, [])
              OR 'NET_ADMIN' IN coalesce(container.added_capabilities, [])
              OR size(coalesce(container.host_ports, [])) > 0
       }
      )
    OPTIONAL MATCH p2=(container:KubernetesContainer)-[:WORKLOAD_PARENT]->(pod)
    RETURN *
    """,
    cypher_count_query="""
    MATCH (pod:KubernetesPod)-[:USES_SERVICE_ACCOUNT]->(:KubernetesServiceAccount)
          -[:WORKLOAD_IDENTITY_BINDING]->(:GCPServiceAccount)
    WHERE NOT pod.namespace IN ['kube-system', 'kube-public', 'kube-node-lease']
    RETURN COUNT(DISTINCT pod) AS count
    """,
    asset_id_field="pod_id",
    module=Module.KUBERNETES,
    maturity=Maturity.EXPERIMENTAL,
)


class PrivilegedKubernetesWorkloadCloudIdentity(Finding):
    pod_id: str | None = None
    pod_name: str | None = None
    namespace: str | None = None
    cluster_name: str | None = None
    service_account: str | None = None
    cloud_identity: str | None = None
    cloud_provider: str | None = None
    privilege_reasons: list[str] | None = None


privileged_kubernetes_workload_cloud_identity = Rule(
    id="privileged_kubernetes_workload_cloud_identity",
    name="Privileged Kubernetes Workload With Cloud Identity",
    description=(
        "Kubernetes workloads that combine host-level or privilege-escalation "
        "settings with a bound cloud identity outside standard Kubernetes "
        "system namespaces. This is a graph-backed compound risk because a pod "
        "escape or workload compromise can become cloud control-plane access."
    ),
    output_model=PrivilegedKubernetesWorkloadCloudIdentity,
    facts=(
        _k8s_privileged_workloads_with_aws_identity,
        _k8s_privileged_workloads_with_gcp_identity,
    ),
    tags=(
        "kubernetes",
        "iam",
        "attack_surface",
        "stride:elevation_of_privilege",
        "stride:spoofing",
    ),
    version="0.1.0",
    frameworks=(
        iso27001_annex_a("5.18"),
        iso27001_annex_a("8.9"),
    ),
)
