# Kubernetes Configuration

## Authentication

1. Configure a [kubeconfig file](https://kubernetes.io/docs/concepts/configuration/organize-cluster-access-kubeconfig/) specifying access to one or multiple clusters.
   Access to multiple Kubernetes clusters can be organized in one kubeconfig
   file. Cartography automatically detects and attempts to sync each cluster.
2. Note the path to the kubeconfig file.

## Required Permissions

Cartography's Kubernetes module requires read-only access to the following Kubernetes API calls:

- `get namespaces` for reading `kube-system` cluster metadata
- `list namespaces`
- `list nodes` for reading node architecture (used to resolve container images)
- `list pods`
- `list services`
- `list serviceaccounts`
- `list persistentvolumes`
- `list persistentvolumeclaims`
- `list storageclasses` in the `storage.k8s.io` group: required to map pod mounts through `PersistentVolumeClaim` and `PersistentVolume` resources to their storage class and CSI driver. Until v1.0.0, if these verbs are missing Cartography logs a warning and skips persistent storage ingestion and cleanup so previously synced storage nodes are preserved; from v1.0.0 a missing verb will be a hard failure.
- `list roles`
- `list rolebindings`
- `list clusterroles`
- `list clusterrolebindings`
- `list ingresses`
- `list deployments`, `list replicasets`, `list statefulsets`, `list daemonsets` in the `apps` group and `list jobs`, `list cronjobs` in the `batch` group: required to ingest the workload controllers (`KubernetesDeployment`, `KubernetesReplicaSet`, `KubernetesStatefulSet`, `KubernetesDaemonSet`, `KubernetesJob`, `KubernetesCronJob`) and the `WORKLOAD_PARENT` chain that climbs from a pod through its controller (`Pod -> Deployment / StatefulSet / DaemonSet / Job -> Namespace`, with the intermediate `ReplicaSet` collapsed and `Job -> CronJob` for batch workloads). Until v1.0.0, if these verbs are missing Cartography logs a warning and skips the workload sync (and its cleanup) so existing graphs are not broken or wiped on upgrade, and pods fall back to a namespace `WORKLOAD_PARENT`; from v1.0.0 a missing verb will be a hard failure.
- `list networkpolicies` in the `networking.k8s.io` group: required to ingest `KubernetesNetworkPolicy` and the `(:KubernetesNetworkPolicy)-[:APPLIES_TO]->(:KubernetesPod)` edges used to reason about namespace segmentation. Until v1.0.0, if the verb is missing Cartography logs a warning and skips NetworkPolicy ingestion and its cleanup, so previously synced `KubernetesNetworkPolicy` nodes are preserved rather than wiped and namespaces are not silently modeled as unsegmented; from v1.0.0 a missing verb will be a hard failure.
- `list gateways` and `list httproutes` in the `gateway.networking.k8s.io` group: required to ingest `KubernetesGateway` and `KubernetesHTTPRoute` and the `Gateway -[:ROUTES]-> HTTPRoute -[:TARGETS]-> Service` traffic path. The Gateway API CRDs are not installed on every cluster; when the CRDs are absent Cartography logs an info message and treats Gateway API as empty for that sync (previously synced `KubernetesGateway`/`KubernetesHTTPRoute` nodes are cleaned up as stale), which is expected and stays supported. Until v1.0.0, if the CRDs are present but the verbs are missing Cartography logs a warning and skips Gateway API ingestion and cleanup so previously synced nodes are preserved; from v1.0.0 a missing verb (with the CRDs present) will be a hard failure.
- `get configmaps` (EKS only): required to ingest legacy IAM identity mappings from the `aws-auth` ConfigMap in `kube-system`. Cartography processes the `mapRoles`, `mapUsers`, and `mapAccounts` fields. For `mapAccounts`, every IAM principal already synced from a listed AWS account (users, roles, and the account root principal) is mapped to a `KubernetesUser` named after the principal ARN (with no Kubernetes groups), so the AWS account must be synced for these mappings to resolve. When the ConfigMap does not exist (clusters using [EKS Access Entries](https://docs.aws.amazon.com/eks/latest/userguide/access-entries.html) exclusively), Cartography logs an info message and continues with Access Entries and external OIDC providers, which is expected and stays supported. Until v1.0.0, if the verb is missing Cartography logs a warning and continues without legacy mappings; from v1.0.0 a missing verb will be a hard failure. Note that the EKS identity sync still runs its cleanup over `KubernetesUser` and `KubernetesGroup`: mappings that previously came only from `aws-auth` (not re-asserted by Access Entries in the current run) are removed from the graph.

## Optional Permissions

The permission below is genuinely optional: withholding it is a supported long-term configuration (not a transitional grace period), because it carries a data-exposure trade-off. Cartography logs a warning and skips the corresponding step, including its cleanup, so previously synced nodes are preserved.

- `list secrets` enables ingestion of `KubernetesSecret` metadata (name,
  namespace, type, and owner references). Kubernetes RBAC has no verb that
  exposes secret metadata without also exposing the content. Granting
  `list secrets` also authorizes reading the base64-encoded `data` field of
  every secret in scope. Cartography never reads or stores secret content,
  but any identity with this permission can. When omitted, Cartography skips
  `sync_secrets`, including cleanup, so previously synced
  `KubernetesSecret` nodes are preserved.

Create a ClusterRole and bind it to the identity used by Cartography. The
example includes both required and recommended optional permissions:

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: cartography-viewer
rules:
# Namespaces - list for namespace sync, get for kube-system cluster metadata
- apiGroups: [""]
  resources:
    - namespaces
  verbs: ["get", "list"]
# Core resources - list only
- apiGroups: [""]
  resources:
    - nodes
    - pods
    - services
    - serviceaccounts
  verbs: ["list"]
# Persistent storage (required). Until v1.0.0 Cartography tolerates these verbs
# being withheld and preserves existing storage nodes; from v1.0.0 a missing
# verb is a hard failure.
- apiGroups: [""]
  resources:
    - persistentvolumes
    - persistentvolumeclaims
  verbs: ["list"]
- apiGroups: ["storage.k8s.io"]
  resources:
    - storageclasses
  verbs: ["list"]
# Secrets (optional): omit if you don't want to grant cluster-wide read access
# to secret contents. Kubernetes RBAC has no metadata-only verb: `list secrets`
# also exposes the base64 `data` field. Cartography ingests metadata only, but any
# identity with this permission can read the content. See the Optional Permissions
# section above for the behavior when this verb is omitted.
- apiGroups: [""]
  resources:
    - secrets
  verbs: ["list"]
# Workload controllers (required): enable the WORKLOAD_PARENT chain from a pod
# up to its owning controller. Until v1.0.0 Cartography tolerates these verbs
# being withheld (warns and skips the workload sync + cleanup, pods fall back to
# a namespace WORKLOAD_PARENT); from v1.0.0 a missing verb is a hard failure.
- apiGroups: ["apps"]
  resources:
    - deployments
    - replicasets
    - statefulsets
    - daemonsets
  verbs: ["list"]
- apiGroups: ["batch"]
  resources:
    - jobs
    - cronjobs
  verbs: ["list"]
# RBAC resources
- apiGroups: ["rbac.authorization.k8s.io"]
  resources:
    - roles
    - rolebindings
    - clusterroles
    - clusterrolebindings
  verbs: ["list"]
# Networking resources
- apiGroups: ["networking.k8s.io"]
  resources:
    - ingresses
    - networkpolicies
  verbs: ["list"]
# Gateway API resources (required). Only apply when the Gateway API CRDs are
# installed in the cluster (a genuinely absent CRD stays a supported no-op).
# Until v1.0.0 a missing verb is tolerated (warn + skip ingestion and cleanup);
# from v1.0.0 it is a hard failure. See the Required Permissions section above.
- apiGroups: ["gateway.networking.k8s.io"]
  resources:
    - gateways
    - httproutes
  verbs: ["list"]
# ConfigMaps (EKS only, required). Used to read the aws-auth ConfigMap for
# legacy IAM identity mappings (a genuinely absent aws-auth ConfigMap stays a
# supported no-op on Access-Entry-only clusters). Until v1.0.0 a missing verb is
# tolerated (warn + continue without legacy mappings); from v1.0.0 it is a hard
# failure. See the Required Permissions section above.
- apiGroups: [""]
  resources:
    - configmaps
  verbs: ["get"]
```

The `/version` endpoint (used to detect the cluster version) requires no additional RBAC: it is accessible by default via the `system:public-info-viewer` ClusterRole.

For Amazon EKS, additional AWS permissions are optional unless you set
`--managed-kubernetes eks`.

If you run Cartography against Amazon EKS and set `--managed-kubernetes eks`, Cartography also enriches cluster access metadata by calling the EKS API for:

- Access Entries
- External OIDC identity provider configs

Grant the AWS principal running Cartography these IAM actions on each target cluster:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "eks:ListAccessEntries",
        "eks:DescribeAccessEntry",
        "eks:ListIdentityProviderConfigs",
        "eks:DescribeIdentityProviderConfig"
      ],
      "Resource": "*"
    }
  ]
}
```

Notes:

- These AWS permissions are in addition to the Kubernetes RBAC above.
- Cartography derives the EKS region from the `cluster` field of each kubeconfig context entry. When using `aws eks update-kubeconfig`, this field is automatically set to the cluster ARN.
- If you use `aws eks update-kubeconfig` to generate the kubeconfig that Cartography consumes, that command also requires `eks:DescribeCluster`.

## Configure Cartography

Pass the kubeconfig path with `--k8s-kubeconfig`. To enrich Amazon EKS access
metadata, also set `--managed-kubernetes eks`.

## Run Cartography

```bash
cartography \
  --selected-modules kubernetes \
  --k8s-kubeconfig /path/to/kubeconfig
```

For Amazon EKS:

```bash
cartography \
  --selected-modules kubernetes \
  --k8s-kubeconfig /path/to/kubeconfig \
  --managed-kubernetes eks
```

## Troubleshooting

When Kubernetes API server cert settings are misconfigured, sync failures can be difficult to diagnose from raw kubeconfig alone. Cartography writes kubeconfig TLS posture fields onto `KubernetesCluster` so operators can quickly reason about configuration risk.

Run these commands before syncing:

```bash
kubectl config view --raw -o json
kubectl get --raw=/version
```

Pay attention to contexts where:
- `insecure-skip-tls-verify=true`
- neither `certificate-authority` nor `certificate-authority-data` is set

Use the [Kubernetes query guide](queries.md) to inspect the captured TLS posture
after a successful sync.

## References

- [Kubernetes kubeconfig documentation](https://kubernetes.io/docs/concepts/configuration/organize-cluster-access-kubeconfig/)
- [Amazon EKS access entries](https://docs.aws.amazon.com/eks/latest/userguide/access-entries.html)
