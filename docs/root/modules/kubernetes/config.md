## Kubernetes Configuration

Follow these steps to analyze Kubernetes objects in Cartography.

1. Configure a [kubeconfig file](https://kubernetes.io/docs/concepts/configuration/organize-cluster-access-kubeconfig/) specifying access to one or multiple clusters.
    - Access to multiple Kubernetes clusters can be organized in a single kubeconfig file. Cartography's Kubernetes intel module will automatically detect that and attempt to sync each cluster.
2. Note down the path of configured kubeconfig file and pass it to cartography CLI with `--k8s-kubeconfig` parameter.

### Required Permissions

Cartography's Kubernetes module requires read-only access to the following Kubernetes API calls:

- `get namespaces` for reading `kube-system` cluster metadata
- `list namespaces`
- `list nodes` for reading node architecture (used to resolve container images)
- `list pods`
- `list services`
- `list serviceaccounts`
- `list roles`
- `list rolebindings`
- `list clusterroles`
- `list clusterrolebindings`
- `list ingresses`

### Optional Permissions

These permissions are recommended but Cartography degrades gracefully if they are withheld: it logs a warning and skips the corresponding step. See each bullet for the precise behavior, since the trade-off differs per resource.

- `list gateways` and `list httproutes` in the `gateway.networking.k8s.io` group — enables ingestion of `KubernetesGateway` and `KubernetesHTTPRoute` and the `Gateway -[:ROUTES]-> HTTPRoute -[:TARGETS]-> Service` traffic path. The Gateway API CRDs are not installed on most clusters out of the box; if the CRDs are absent Cartography logs an info message and treats Gateway API as empty for the current sync, so previously synced `KubernetesGateway`/`KubernetesHTTPRoute` nodes for that cluster are cleaned up as stale. If the CRDs are present but the verbs are not granted, Cartography logs a warning, skips Gateway API ingestion, skips Gateway API cleanup, and continues with the rest of the cluster sync, preserving any previously synced `KubernetesGateway`/`KubernetesHTTPRoute` nodes.
- `list secrets` — enables ingestion of `KubernetesSecret` metadata (name, namespace, type, owner references). Kubernetes RBAC has no verb that exposes secret metadata without also exposing the content: granting `list secrets` also authorizes reading the base64-encoded `data` field of every secret in scope. Cartography never reads or stores secret content, but any identity with this permission can. Operators who prefer not to grant cluster-wide read access to secret content can omit this verb. When omitted, Cartography skips `sync_secrets` entirely — including the cleanup step — so previously synced `KubernetesSecret` nodes are preserved.
- `get configmaps` (EKS only) — enables ingestion of legacy IAM identity mappings from the `aws-auth` ConfigMap in `kube-system`. This is optional because:
  - Clusters that use [EKS Access Entries](https://docs.aws.amazon.com/eks/latest/userguide/access-entries.html) exclusively may not have an `aws-auth` ConfigMap at all.
  - Some operators prefer not to grant `get` on all ConfigMaps just to read `aws-auth`.

  When omitted or when the ConfigMap does not exist, Cartography still ingests identity mappings from EKS Access Entries and external OIDC providers. Note that the EKS identity sync still runs its cleanup step over `KubernetesUser` and `KubernetesGroup`: mappings that previously came only from `aws-auth` (i.e. not also re-asserted by Access Entries in the current run) will be removed from the graph. If you want to preserve legacy `aws-auth` mappings across syncs, grant this verb.

Create a ClusterRole and bind it to the identity used by Cartography:

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
# Secrets (optional) — omit if you don't want to grant cluster-wide read access
# to secret contents. Kubernetes RBAC has no metadata-only verb: `list secrets`
# also exposes the base64 `data` field. Cartography ingests metadata only, but any
# identity with this permission can read the content. See the Optional Permissions
# section above for the behavior when this verb is omitted.
- apiGroups: [""]
  resources:
    - secrets
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
  verbs: ["list"]
# Gateway API resources (optional) — only useful when the Gateway API CRDs are
# installed in the cluster. Cartography skips ingestion gracefully if the CRDs
# are absent or the verbs are not granted. See the Optional Permissions section
# above for behavior when these verbs are withheld.
- apiGroups: ["gateway.networking.k8s.io"]
  resources:
    - gateways
    - httproutes
  verbs: ["list"]
# ConfigMaps (EKS only, optional) — only used to read the aws-auth ConfigMap for
# legacy IAM identity mappings. Omit if your cluster uses EKS Access Entries
# exclusively or if you don't want to grant `get` on all ConfigMaps.
- apiGroups: [""]
  resources:
    - configmaps
  verbs: ["get"]
```

The `/version` endpoint (used to detect the cluster version) requires no additional RBAC — it is accessible by default via the `system:public-info-viewer` ClusterRole.

### Additional AWS Permissions for EKS

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

### TLS Troubleshooting and Validation

When Kubernetes API server cert settings are misconfigured, sync failures can be difficult to diagnose from raw kubeconfig alone. Cartography writes kubeconfig TLS posture fields onto `KubernetesCluster` so operators can quickly reason about configuration risk.

#### Preflight checks

Run these commands before syncing:

```bash
kubectl config view --raw -o json
kubectl get --raw=/version
```

Pay attention to contexts where:
- `insecure-skip-tls-verify=true`
- neither `certificate-authority` nor `certificate-authority-data` is set

#### Graph query for TLS posture

```cypher
MATCH (k:KubernetesCluster)
RETURN k.name, k.api_server_url, k.kubeconfig_tls_configuration_status,
       k.kubeconfig_insecure_skip_tls_verify,
       k.kubeconfig_has_certificate_authority_data,
       k.kubeconfig_has_certificate_authority_file,
       k.kubeconfig_has_client_certificate,
       k.kubeconfig_has_client_key
ORDER BY k.name;
```
