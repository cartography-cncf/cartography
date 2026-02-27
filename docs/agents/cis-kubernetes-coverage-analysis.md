# CIS Kubernetes Benchmark v1.12.0 — Cartography Coverage Analysis

> **Date**: 2026-02-27
> **Benchmark**: CIS Kubernetes Benchmark v1.12.0 (2025-09-26)
> **Target**: Kubernetes v1.32–v1.34
> **Purpose**: Determine which CIS controls can be implemented as Cartography rules based on the data currently ingested by the Kubernetes intel module.

## How Cartography Rules Work

Cartography rules are Cypher queries that run against the Neo4j graph to detect security misconfigurations. A rule can only check for a condition if the relevant data has been ingested into the graph by an intel module. This analysis maps each CIS control to the graph data it would require and determines whether that data is available.

## Kubernetes Graph Data Available in Cartography

The following node types and key properties are ingested by `cartography/intel/kubernetes/`:

| Node Type | Key Properties | Relationships |
|-----------|---------------|---------------|
| `KubernetesCluster` | id, name, version, version_major, version_minor | — |
| `KubernetesNamespace` | uid, name, status_phase, cluster_name | `RESOURCE` ← Cluster |
| `KubernetesPod` | uid, name, status_phase, namespace, node, labels | `RESOURCE` ← Cluster, `CONTAINS` ← Namespace, `USES_SECRET_VOLUME` → Secret, `USES_SECRET_ENV` → Secret |
| `KubernetesContainer` | uid, name, image, namespace, image_pull_policy, cpu/memory request/limit, status_* | `RESOURCE` ← Cluster, `CONTAINS` ← Pod, `CONTAINS` ← Namespace, `HAS_IMAGE` → ECRImage/GitLabContainerImage |
| `KubernetesService` | uid, name, namespace, type, cluster_ip, load_balancer_ip | `RESOURCE` ← Cluster, `TARGETS` → Pod |
| `KubernetesIngress` | uid, name, namespace | `RESOURCE` ← Cluster |
| `KubernetesSecret` | uid, name, namespace, type, composite_id | `RESOURCE` ← Cluster, `CONTAINS` ← Namespace |
| `KubernetesServiceAccount` | id, name, namespace, uid | `RESOURCE` ← Cluster, `CONTAINS` ← Namespace |
| `KubernetesRole` | id, name, namespace, uid, **api_groups**, **resources**, **verbs** | `RESOURCE` ← Cluster |
| `KubernetesClusterRole` | id, name, uid, **api_groups**, **resources**, **verbs** | `RESOURCE` ← Cluster |
| `KubernetesRoleBinding` | id, name, namespace, role_name, role_kind, role_id | `RESOURCE` ← Cluster, `SUBJECT` → SA/User/Group, `ROLE_REF` → Role |
| `KubernetesClusterRoleBinding` | id, name, role_name, role_kind, role_id | `RESOURCE` ← Cluster, `SUBJECT` → SA/User/Group, `ROLE_REF` → ClusterRole |
| `KubernetesUser` | id, name | `RESOURCE` ← Cluster |
| `KubernetesGroup` | id, name | `RESOURCE` ← Cluster |

### Data NOT ingested (relevant to CIS controls)

- **Pod security context**: `privileged`, `allowPrivilegeEscalation`, `runAsNonRoot`, `runAsUser`, `runAsGroup`, `readOnlyRootFilesystem`, `seccompProfile`
- **Pod host sharing**: `hostPID`, `hostIPC`, `hostNetwork`
- **Container capabilities**: `add`, `drop` (Linux capabilities)
- **Container ports**: `hostPort`
- **Volume types**: `hostPath` presence
- **Service account token mounting**: `automountServiceAccountToken`
- **Control plane configuration**: API server flags, controller-manager flags, scheduler flags
- **Node-level configuration**: kubelet flags, file permissions, etcd config
- **Network policies**: `NetworkPolicy` objects
- **Admission controllers**: PSA labels, webhook configurations
- **RBAC sub-resources**: roles store `resources` as a flat list — sub-resources like `nodes/proxy` or `serviceaccounts/token` may or may not be preserved as-is (needs verification)

---

## Section 1: Control Plane Components (51 controls)

These controls check file permissions, file ownership, and API server / controller-manager / scheduler process flags on the control plane node. Cartography does not SSH into nodes or inspect process arguments — none of these are coverable.

### 1.1 Control Plane Node Configuration Files (21 controls)

| # | Control | Coverable | Data Required |
|---|---------|:---------:|---------------|
| 1.1.1 | API server pod spec file permissions ≤ 600 | No | Host file: `/etc/kubernetes/manifests/kube-apiserver.yaml` permissions |
| 1.1.2 | API server pod spec file ownership = root:root | No | Host file ownership |
| 1.1.3 | Controller manager pod spec file permissions ≤ 600 | No | Host file permissions |
| 1.1.4 | Controller manager pod spec file ownership = root:root | No | Host file ownership |
| 1.1.5 | Scheduler pod spec file permissions ≤ 600 | No | Host file permissions |
| 1.1.6 | Scheduler pod spec file ownership = root:root | No | Host file ownership |
| 1.1.7 | etcd pod spec file permissions ≤ 600 | No | Host file permissions |
| 1.1.8 | etcd pod spec file ownership = root:root | No | Host file ownership |
| 1.1.9 | CNI file permissions ≤ 600 | No | Host file permissions |
| 1.1.10 | CNI file ownership = root:root | No | Host file ownership |
| 1.1.11 | etcd data directory permissions ≤ 700 | No | Host directory permissions |
| 1.1.12 | etcd data directory ownership = etcd:etcd | No | Host directory ownership |
| 1.1.13 | admin.conf file permissions = 600 | No | Host file permissions |
| 1.1.14 | admin.conf file ownership = root:root | No | Host file ownership |
| 1.1.15 | scheduler.conf file permissions ≤ 600 | No | Host file permissions |
| 1.1.16 | scheduler.conf file ownership = root:root | No | Host file ownership |
| 1.1.17 | controller-manager.conf file permissions ≤ 600 | No | Host file permissions |
| 1.1.18 | controller-manager.conf file ownership = root:root | No | Host file ownership |
| 1.1.19 | PKI directory ownership = root:root | No | Host directory ownership |
| 1.1.20 | PKI certificate file permissions ≤ 644 | No | Host file permissions |
| 1.1.21 | PKI key file permissions = 600 | No | Host file permissions |

### 1.2 API Server (30 controls)

| # | Control | Coverable | Data Required |
|---|---------|:---------:|---------------|
| 1.2.1 | `--anonymous-auth` = false | No | API server flag |
| 1.2.2 | `--token-auth-file` not set | No | API server flag |
| 1.2.3 | DenyServiceExternalIPs is set | No | Admission controller config |
| 1.2.4 | `--kubelet-client-certificate` and `--kubelet-client-key` set | No | API server flags |
| 1.2.5 | `--kubelet-certificate-authority` set | No | API server flag |
| 1.2.6 | `--authorization-mode` ≠ AlwaysAllow | No | API server flag |
| 1.2.7 | `--authorization-mode` includes Node | No | API server flag |
| 1.2.8 | `--authorization-mode` includes RBAC | No | API server flag |
| 1.2.9 | EventRateLimit admission plugin set | No | Admission controller config |
| 1.2.10 | AlwaysAdmit admission plugin not set | No | Admission controller config |
| 1.2.11 | AlwaysPullImages admission plugin set | No | Admission controller config |
| 1.2.12 | ServiceAccount admission plugin set | No | Admission controller config |
| 1.2.13 | NamespaceLifecycle admission plugin set | No | Admission controller config |
| 1.2.14 | NodeRestriction admission plugin set | No | Admission controller config |
| 1.2.15 | `--profiling` = false | No | API server flag |
| 1.2.16 | `--audit-log-path` set | No | API server flag |
| 1.2.17 | `--audit-log-maxage` ≥ 30 | No | API server flag |
| 1.2.18 | `--audit-log-maxbackup` ≥ 10 | No | API server flag |
| 1.2.19 | `--audit-log-maxsize` ≥ 100 | No | API server flag |
| 1.2.20 | `--request-timeout` set appropriately | No | API server flag |
| 1.2.21 | `--service-account-lookup` = true | No | API server flag |
| 1.2.22 | `--service-account-key-file` set | No | API server flag |
| 1.2.23 | `--etcd-certfile` and `--etcd-keyfile` set | No | API server flags |
| 1.2.24 | `--tls-cert-file` and `--tls-private-key-file` set | No | API server flags |
| 1.2.25 | `--client-ca-file` set | No | API server flag |
| 1.2.26 | `--etcd-cafile` set | No | API server flag |
| 1.2.27 | `--encryption-provider-config` set | No | API server flag |
| 1.2.28 | Encryption providers appropriately configured | No | EncryptionConfiguration resource |
| 1.2.29 | Strong cryptographic ciphers only | No | API server TLS config |
| 1.2.30 | `--service-account-extend-token-expiration` = false | No | API server flag |

### 1.3 Controller Manager (7 controls)

| # | Control | Coverable | Data Required |
|---|---------|:---------:|---------------|
| 1.3.1 | `--terminated-pod-gc-threshold` set | No | Controller manager flag |
| 1.3.2 | `--profiling` = false | No | Controller manager flag |
| 1.3.3 | `--use-service-account-credentials` = true | No | Controller manager flag |
| 1.3.4 | `--service-account-private-key-file` set | No | Controller manager flag |
| 1.3.5 | `--root-ca-file` set | No | Controller manager flag |
| 1.3.6 | RotateKubeletServerCertificate = true | No | Controller manager flag |
| 1.3.7 | `--bind-address` = 127.0.0.1 | No | Controller manager flag |

### 1.4 Scheduler (2 controls)

| # | Control | Coverable | Data Required |
|---|---------|:---------:|---------------|
| 1.4.1 | `--profiling` = false | No | Scheduler flag |
| 1.4.2 | `--bind-address` = 127.0.0.1 | No | Scheduler flag |

**Section 1 total: 0 / 51 coverable**

---

## Section 2: etcd (7 controls)

These controls check etcd process flags for TLS and authentication settings. Cartography does not inspect etcd configuration.

| # | Control | Coverable | Data Required |
|---|---------|:---------:|---------------|
| 2.1 | `--cert-file` and `--key-file` set | No | etcd flags |
| 2.2 | `--client-cert-auth` = true | No | etcd flag |
| 2.3 | `--auto-tls` ≠ true | No | etcd flag |
| 2.4 | `--peer-cert-file` and `--peer-key-file` set | No | etcd flags |
| 2.5 | `--peer-client-cert-auth` = true | No | etcd flag |
| 2.6 | `--peer-auto-tls` ≠ true | No | etcd flag |
| 2.7 | Unique CA for etcd | No | etcd TLS config |

**Section 2 total: 0 / 7 coverable**

---

## Section 3: Control Plane Configuration (5 controls)

| # | Control | Coverable | Data Required |
|---|---------|:---------:|---------------|
| 3.1.1 | Client cert authentication not used for users | No | Auth config / credential review |
| 3.1.2 | SA token authentication not used for users | No | Auth config |
| 3.1.3 | Bootstrap token authentication not used for users | No | Auth config |
| 3.2.1 | Minimal audit policy created | No | Audit policy YAML |
| 3.2.2 | Audit policy covers key security concerns | No | Audit policy YAML |

**Section 3 total: 0 / 5 coverable**

---

## Section 4: Worker Nodes (24 controls)

These controls check worker node file permissions and kubelet configuration. Cartography does not SSH into nodes or inspect kubelet settings.

### 4.1 Worker Node Configuration Files (10 controls)

| # | Control | Coverable | Data Required |
|---|---------|:---------:|---------------|
| 4.1.1 | kubelet service file permissions ≤ 600 | No | Host file permissions |
| 4.1.2 | kubelet service file ownership = root:root | No | Host file ownership |
| 4.1.3 | Proxy kubeconfig file permissions ≤ 600 | No | Host file permissions |
| 4.1.4 | Proxy kubeconfig file ownership = root:root | No | Host file ownership |
| 4.1.5 | kubelet.conf file permissions ≤ 600 | No | Host file permissions |
| 4.1.6 | kubelet.conf file ownership = root:root | No | Host file ownership |
| 4.1.7 | CA file permissions ≤ 644 | No | Host file permissions |
| 4.1.8 | Client CA file ownership = root:root | No | Host file ownership |
| 4.1.9 | kubelet config.yaml permissions ≤ 600 | No | Host file permissions |
| 4.1.10 | kubelet config.yaml ownership = root:root | No | Host file ownership |

### 4.2 Kubelet (14 controls)

| # | Control | Coverable | Data Required |
|---|---------|:---------:|---------------|
| 4.2.1 | `--anonymous-auth` = false | No | Kubelet flag |
| 4.2.2 | `--authorization-mode` ≠ AlwaysAllow | No | Kubelet flag |
| 4.2.3 | `--client-ca-file` set | No | Kubelet flag |
| 4.2.4 | readOnlyPort = 0 | No | Kubelet config |
| 4.2.5 | `--streaming-connection-idle-timeout` ≠ 0 | No | Kubelet flag |
| 4.2.6 | `--make-iptables-util-chains` = true | No | Kubelet flag |
| 4.2.7 | `--hostname-override` not set | No | Kubelet flag |
| 4.2.8 | eventRecordQPS set appropriately | No | Kubelet config |
| 4.2.9 | `--tls-cert-file` and `--tls-private-key-file` set | No | Kubelet flags |
| 4.2.10 | `--rotate-certificates` ≠ false | No | Kubelet flag |
| 4.2.11 | RotateKubeletServerCertificate = true | No | Kubelet config |
| 4.2.12 | Strong cryptographic ciphers only | No | Kubelet TLS config |
| 4.2.13 | Limit on pod PIDs | No | Kubelet config |
| 4.2.14 | `--seccomp-default` = true | No | Kubelet flag |

### 4.3 kube-proxy (1 control)

| # | Control | Coverable | Data Required |
|---|---------|:---------:|---------------|
| 4.3.1 | kube-proxy metrics service bound to localhost | No | kube-proxy config |

**Section 4 total: 0 / 24 coverable**

---

## Section 5: Policies (31 controls)

This is the section where Cartography has relevant graph data, primarily around RBAC, secrets, and workload placement.

### 5.1 RBAC and Service Accounts (13 controls)

| # | Control | Coverable | Cypher Strategy | Notes |
|---|---------|:---------:|-----------------|-------|
| **5.1.1** | cluster-admin role only used where required | **Yes** | Match `KubernetesClusterRoleBinding` with `role_name = 'cluster-admin'`, list all subjects (SA, User, Group) bound to it | Can flag non-system bindings |
| **5.1.2** | Minimize access to secrets | **Yes** | Match `KubernetesClusterRole`/`KubernetesRole` where `'secrets' IN resources` AND any of `get/list/watch` in verbs | Excludes system controllers by convention |
| **5.1.3** | Minimize wildcard use in Roles/ClusterRoles | **Yes** | Match roles where `'*' IN resources` OR `'*' IN verbs` | Straightforward property check |
| **5.1.4** | Minimize access to create pods | **Yes** | Match roles where `'pods' IN resources` AND `'create' IN verbs` | |
| **5.1.5** | Default SA not actively used | **Partial** | Match `KubernetesServiceAccount` with `name = 'default'` that has SUBJECT rels from RoleBindings/ClusterRoleBindings (beyond default) | Cannot verify `automountServiceAccountToken: false` — not ingested |
| **5.1.6** | SA tokens only mounted where necessary | **No** | — | Requires `automountServiceAccountToken` on pods and SAs — not ingested |
| **5.1.7** | Avoid system:masters group | **Yes** | Match `KubernetesGroup` with `name` ending in `system:masters`, list all bindings via SUBJECT rels | Can detect non-default bindings |
| **5.1.8** | Limit bind/impersonate/escalate permissions | **Yes** | Match roles where verbs contain `bind`, `impersonate`, or `escalate` | |
| **5.1.9** | Minimize access to create persistent volumes | **Yes** | Match roles where `'persistentvolumes' IN resources` AND `'create' IN verbs` | |
| **5.1.10** | Minimize access to nodes/proxy sub-resource | **Partial** | Match roles where resources contain `nodes/proxy` | Depends on whether sub-resources are preserved in the `resources` list during ingestion. Needs verification. |
| **5.1.11** | Minimize CSR approval access | **Partial** | Match roles where resources contain `certificatesigningrequests/approval` | Same sub-resource caveat |
| **5.1.12** | Minimize webhook config access | **Yes** | Match roles where resources contain `validatingwebhookconfigurations` or `mutatingwebhookconfigurations` | Full resource names should be present |
| **5.1.13** | Minimize SA token creation access | **Partial** | Match roles where resources contain `serviceaccounts/token` | Same sub-resource caveat |

### 5.2 Pod Security Standards (12 controls)

| # | Control | Coverable | Data Required |
|---|---------|:---------:|---------------|
| 5.2.1 | Active policy control mechanism in place | No | Admission controller / PSA label config |
| 5.2.2 | No privileged containers | No | `securityContext.privileged` on containers — not ingested |
| 5.2.3 | No hostPID sharing | No | `spec.hostPID` on pods — not ingested |
| 5.2.4 | No hostIPC sharing | No | `spec.hostIPC` on pods — not ingested |
| 5.2.5 | No hostNetwork sharing | No | `spec.hostNetwork` on pods — not ingested |
| 5.2.6 | No allowPrivilegeEscalation | No | `securityContext.allowPrivilegeEscalation` — not ingested |
| 5.2.7 | No root containers | No | `securityContext.runAsNonRoot` / `runAsUser` — not ingested |
| 5.2.8 | No NET_RAW capability | No | `securityContext.capabilities` — not ingested |
| 5.2.9 | Minimize capabilities | No | `securityContext.capabilities` — not ingested |
| 5.2.10 | No Windows HostProcess containers | No | `windowsOptions.hostProcess` — not ingested |
| 5.2.11 | No HostPath volumes | No | `volumes[].hostPath` — not ingested |
| 5.2.12 | No HostPorts on containers | No | `containers[].ports[].hostPort` — not ingested |

### 5.3 Network Policies and CNI (2 controls)

| # | Control | Coverable | Data Required |
|---|---------|:---------:|---------------|
| 5.3.1 | CNI supports NetworkPolicies | No | CNI plugin configuration |
| 5.3.2 | All namespaces have NetworkPolicies | No | `NetworkPolicy` objects — not ingested |

### 5.4 Secrets Management (2 controls)

| # | Control | Coverable | Cypher Strategy | Notes |
|---|---------|:---------:|-----------------|-------|
| **5.4.1** | Prefer secrets as files over env vars | **Yes** | Match pods that have `USES_SECRET_ENV` rels but no `USES_SECRET_VOLUME` rels to the same secret | Pod-to-secret relationships are ingested separately for volume mounts and env vars |
| 5.4.2 | Consider external secret storage | No | Architectural recommendation — not a pass/fail check |

### 5.5 Extensible Admission Control (1 control)

| # | Control | Coverable | Data Required |
|---|---------|:---------:|---------------|
| 5.5.1 | ImagePolicyWebhook configured | No | Admission controller config |

### 5.6 General Policies (4 controls)

| # | Control | Coverable | Cypher Strategy | Notes |
|---|---------|:---------:|-----------------|-------|
| 5.6.1 | Administrative boundaries via namespaces | No | Organizational recommendation — cannot be expressed as pass/fail |
| 5.6.2 | Seccomp profile set to docker/default | No | `securityContext.seccompProfile` — not ingested |
| 5.6.3 | Security context applied to pods/containers | No | Security context fields — not ingested |
| **5.6.4** | Default namespace not used | **Yes** | Match `KubernetesPod` where `namespace = 'default'` | Straightforward |

**Section 5 total: 10 coverable + 4 partial / 31 controls**

---

## Summary

| Section | Controls | Coverable | Partial | Not Coverable | Coverage |
|---------|:--------:|:---------:|:-------:|:-------------:|:--------:|
| 1. Control Plane Components | 51 | 0 | 0 | 51 | 0% |
| 2. etcd | 7 | 0 | 0 | 7 | 0% |
| 3. Control Plane Configuration | 5 | 0 | 0 | 5 | 0% |
| 4. Worker Nodes | 24 | 0 | 0 | 24 | 0% |
| 5.1 RBAC & Service Accounts | 13 | 8 | 4 | 1 | 62–92% |
| 5.2 Pod Security Standards | 12 | 0 | 0 | 12 | 0% |
| 5.3 Network Policies & CNI | 2 | 0 | 0 | 2 | 0% |
| 5.4 Secrets Management | 2 | 1 | 0 | 1 | 50% |
| 5.5 Extensible Admission Control | 1 | 0 | 0 | 1 | 0% |
| 5.6 General Policies | 4 | 1 | 0 | 3 | 25% |
| **Total** | **121** | **10** | **4** | **107** | **8–12%** |

### Why only Section 5 is coverable

Sections 1–4 are **infrastructure-level controls**: they check file permissions on cluster nodes, process flags on API server / controller-manager / scheduler / kubelet / etcd, and host-level configuration. Cartography's Kubernetes intel module collects data via the **Kubernetes API** (listing pods, services, RBAC objects, etc.), not by SSH-ing into nodes or inspecting process arguments. These controls are the domain of tools like kube-bench, which run directly on cluster nodes.

Section 5 contains **policy-level controls** that can be evaluated by querying the Kubernetes API objects — which is exactly what Cartography ingests. Within Section 5, the RBAC subsection (5.1) has the best coverage because Cartography fully ingests Roles, ClusterRoles, RoleBindings, and ClusterRoleBindings with their verbs, resources, and api_groups.

Section 5.2 (Pod Security Standards) is not coverable because the Kubernetes intel module does not currently extract `securityContext`, `hostPID`, `hostIPC`, `hostNetwork`, capabilities, or volume types from pods/containers.

### Implementation plan: 10 solid rules + 4 partial

The following rules will be implemented as Cartography rules with `Framework(short_name="CIS", scope="kubernetes", revision="1.12")`:

| Rule ID | CIS Control | Description | Maturity |
|---------|-------------|-------------|----------|
| `cis_k8s_5_1_1_cluster_admin_usage` | 5.1.1 | Detect non-essential cluster-admin bindings | EXPERIMENTAL |
| `cis_k8s_5_1_2_secret_access` | 5.1.2 | Detect roles granting get/list/watch on secrets | EXPERIMENTAL |
| `cis_k8s_5_1_3_wildcard_roles` | 5.1.3 | Detect wildcard `*` in roles/clusterroles | EXPERIMENTAL |
| `cis_k8s_5_1_4_pod_create_access` | 5.1.4 | Detect roles granting pod creation | EXPERIMENTAL |
| `cis_k8s_5_1_5_default_sa_bindings` | 5.1.5 | Detect non-default bindings to default SA | EXPERIMENTAL |
| `cis_k8s_5_1_7_system_masters_group` | 5.1.7 | Detect bindings to system:masters group | EXPERIMENTAL |
| `cis_k8s_5_1_8_escalation_permissions` | 5.1.8 | Detect bind/impersonate/escalate in roles | EXPERIMENTAL |
| `cis_k8s_5_1_9_pv_create_access` | 5.1.9 | Detect roles granting PV creation | EXPERIMENTAL |
| `cis_k8s_5_1_12_webhook_config_access` | 5.1.12 | Detect roles granting webhook config access | EXPERIMENTAL |
| `cis_k8s_5_4_1_secrets_in_env_vars` | 5.4.1 | Detect pods using secrets via env vars | EXPERIMENTAL |
| `cis_k8s_5_6_4_default_namespace` | 5.6.4 | Detect pods running in default namespace | EXPERIMENTAL |

Partial rules (sub-resource dependent — to be verified during implementation):

| Rule ID | CIS Control | Description | Blocker |
|---------|-------------|-------------|---------|
| `cis_k8s_5_1_10_node_proxy_access` | 5.1.10 | Detect roles with nodes/proxy access | Sub-resource format in graph |
| `cis_k8s_5_1_11_csr_approval_access` | 5.1.11 | Detect roles with CSR approval access | Sub-resource format in graph |
| `cis_k8s_5_1_13_sa_token_creation` | 5.1.13 | Detect roles with SA token creation | Sub-resource format in graph |

### Future coverage improvements

To increase CIS Kubernetes coverage, the following data ingestion enhancements would unlock the most additional controls:

| Enhancement | Controls Unlocked | Effort |
|-------------|:-----------------:|--------|
| Ingest pod `securityContext` fields (privileged, runAsNonRoot, allowPrivilegeEscalation) | 5.2.2, 5.2.6, 5.2.7 | Medium |
| Ingest pod host sharing flags (hostPID, hostIPC, hostNetwork) | 5.2.3, 5.2.4, 5.2.5 | Low |
| Ingest container capabilities (add/drop) | 5.2.8, 5.2.9 | Medium |
| Ingest container ports (hostPort) | 5.2.12 | Low |
| Ingest volume types (hostPath) | 5.2.11 | Low |
| Ingest `automountServiceAccountToken` on SA and pods | 5.1.5 (full), 5.1.6 | Low |
| Ingest NetworkPolicy objects | 5.3.2 | Medium |
