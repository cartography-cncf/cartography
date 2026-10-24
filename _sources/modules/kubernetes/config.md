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
- The AWS managed `SecurityAudit` policy includes `eks:ListAccessEntries` and
  `eks:DescribeAccessEntry`. If the principal already has `SecurityAudit`, grant
  only `eks:ListIdentityProviderConfigs` and `eks:DescribeIdentityProviderConfig`.
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

## GKE

Cartography can connect GKE clusters to the GCP graph. Two different control planes are
involved, each with its own authorization:

| Control plane | Endpoint | Used for | Authorized by |
| --- | --- | --- | --- |
| GKE API | `container.googleapis.com` | Reading the cluster's GKE metadata (endpoints, CA, workload pool) | Google IAM: `container.clusters.get` |
| Kubernetes API server | The cluster's DNS or IP endpoint | Listing Kubernetes objects | Google IAM (GKE's IAM authorizer) **or** Kubernetes RBAC, plus `container.clusters.connect` for the DNS endpoint |

### Connecting with Google credentials (`--gke-cluster`)

`--gke-cluster` connects without a kubeconfig, using Application Default Credentials
(ADC): an attached service account, federated credentials, or
`gcloud auth application-default login`.

```bash
cartography --neo4j-uri bolt://localhost:7687 \
  --selected-modules kubernetes \
  --gke-cluster projects/example-project/locations/us-central1/clusters/example \
  --gke-impersonate-service-account cartography@example-project.iam.gserviceaccount.com
```

- Repeat `--gke-cluster` for more clusters. It accepts
  `projects/PROJECT_ID/locations/LOCATION/clusters/NAME`, a GKE selfLink, or a
  `gke_PROJECT_ID_LOCATION_NAME` kubeconfig context name. Use the project ID, not the
  project number, so the cluster matches the GCP module's `GKECluster`.
- Tokens stay in memory and refresh during ingestion. No kubeconfig is written.
- `--gke-endpoint` picks the Kubernetes API endpoint, with no fallback:
  - `dns` (default): the DNS-based endpoint, verified against public CAs. Requires
    `controlPlaneEndpointsConfig.dnsEndpointConfig.allowExternalTraffic`. It works
    for private clusters, including clusters whose IP endpoints are private or
    disabled, because access is authorized by IAM rather than by network location.
    VPC Service Controls can still restrict it.
  - `private`: the private IP endpoint, verified against the cluster CA. The collector
    must have a network path to that endpoint: run it inside the cluster's VPC (or a
    peered or VPN-connected network), for example on a VM, a CI runner in the VPC, or
    an in-cluster collector. Authorized networks, if enabled, must include the
    collector's address.
  - `public`: the public IP endpoint, verified against the cluster CA. Must be enabled;
    an allocated public IP alone is not enough.
- Clusters with the DNS endpoint disabled and no reachable IP endpoint are not
  supported today. [Connect Gateway](https://cloud.google.com/kubernetes-engine/enterprise/multicluster-management/gateway)
  (for fleet-registered clusters) could serve them in the future.
- A cluster whose GKE metadata cannot be read (missing, or IAM denied) is logged and
  skipped.
- When embedding Cartography, pass a `google.auth` credentials object as
  `Config(gke_credentials=...)` to use it instead of ADC, for example Workload
  Identity Federation credentials built in code. It is combined with
  `gke_impersonate_service_account` when both are set. Federated principals
  (`principal://` and `principalSet://`) can be granted `roles/container.viewer`
  directly; new grants can take a few minutes to reach the DNS endpoint.

Required permissions for the ADC identity (or the impersonated service account):

- GKE API: `container.clusters.get` on each cluster.
- Kubernetes API server: `container.clusters.connect` for the DNS endpoint, and read
  access to the Kubernetes objects listed above. `roles/container.clusterViewer`
  grants `get` and `connect` but **no** Kubernetes object reads. Grant object reads in
  either of two ways:
  - IAM: `roles/container.viewer` (read-only access to Kubernetes objects, without
    Secrets).
  - RBAC: bind the Kubernetes permissions above to a subject of kind `User` named after
    the Google identity that ADC represents: the service account email when using a
    service account or `--gke-impersonate-service-account`, or the user's email for
    user credentials.
- Impersonation: the ADC identity needs `iam.serviceAccounts.getAccessToken` on the
  target service account, usually through `roles/iam.serviceAccountTokenCreator`.
- Optional: `get` on the non-resource URL `/.well-known/openid-configuration` records
  the cluster's ServiceAccount token issuer and JWKS URI on `KubernetesCluster`.

### Kubeconfig with GKE metadata (`--managed-kubernetes gke`)

With an existing kubeconfig, `--managed-kubernetes gke` reads each context's GKE
metadata with Google ADC; kubeconfig still authenticates Kubernetes requests. Each
context's cluster name must be a GKE reference (the `gke_PROJECT_ID_LOCATION_NAME`
names written by `gcloud container clusters get-credentials` work). This needs
`container.clusters.get`; `--gke-impersonate-service-account` only affects that call.

### Graph

Run the GCP module before the Kubernetes module, with GKE, IAM, workload identity,
policy bindings, and Compute enabled. The links below match against GCP nodes that
already exist in the graph.

- `GKECluster -[:MAPS_TO]-> KubernetesCluster`, matched on the GKE resource name.
- `KubernetesNode -[:MEMBER_OF]-> GKENodePool` from the `cloud.google.com/gke-nodepool`
  label, and `KubernetesNode -[:IS_INSTANCE]-> GCPInstance` from `spec.providerID`.
  Autopilot VMs are not visible to the Compute API, so Autopilot nodes have no
  `IS_INSTANCE` edge.
- `KubernetesService`, `KubernetesIngress`, and `KubernetesGateway -[:USES_LOAD_BALANCER]->
  GCPForwardingRule`, matched on the status IP address within the cluster's project.
  Non-public addresses must also be in the cluster's VPC network, so private IPs
  reused across VPCs do not collide. Backend health and firewall reachability are
  not evaluated.
- `GCPPrincipal -[:MAPS_TO]-> KubernetesUser`, matched on email.
- `KubernetesServiceAccount -[:HAS_ALLOW_POLICY]-> GCPPolicyBinding` when a binding
  member names the service account through the cluster's workload pool
  ([member formats](https://cloud.google.com/kubernetes-engine/docs/concepts/workload-identity#principal-id)):
  the namespace/name subject, the ServiceAccount UID, the namespace, the cluster, the
  whole pool, or the legacy `serviceAccount:PROJECT_ID.svc.id.goog[NAMESPACE/NAME]`
  form. The workload pool is shared by every cluster in a project, so namespace/name
  and namespace members also match same-named service accounts in other clusters. IAM
  conditions are not evaluated; `matched_members` lists the members that matched.
- `KubernetesServiceAccount -[:ANNOTATED_SERVICE_ACCOUNT]-> GCPServiceAccount` records
  the `iam.gke.io/gcp-service-account` annotation alone.
- `KubernetesServiceAccount -[:WORKLOAD_IDENTITY_BINDING]-> GCPServiceAccount` requires
  the annotation **and** an unconditional `roles/iam.workloadIdentityUser` binding set
  directly on that Google service account. Grants inherited from the project, folder,
  or organization are not expanded.

```{note}
Before this release, `WORKLOAD_IDENTITY_BINDING` was created from the annotation alone.
Queries that relied on that should use `ANNOTATED_SERVICE_ACCOUNT`. Old annotation-only
edges are removed on the next Kubernetes sync.
```
