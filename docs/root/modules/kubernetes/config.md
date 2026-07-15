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
- `list roles`
- `list rolebindings`
- `list clusterroles`
- `list clusterrolebindings`
- `list ingresses`

## Optional Permissions

These permissions are recommended but can be withheld:

- `list gateways` and `list httproutes` in the
  `gateway.networking.k8s.io` group enables Gateway API ingestion.
- `list networkpolicies` in the `networking.k8s.io` group enables network
  policy ingestion.
- `list secrets` enables secret metadata ingestion. Kubernetes RBAC has no
  metadata-only verb, so this permission also authorizes reading secret
  content even though Cartography never reads or stores that content.
- `get configmaps` enables legacy EKS IAM identity mappings from the
  `aws-auth` ConfigMap. It is unnecessary for clusters that use only
  [EKS Access Entries](https://docs.aws.amazon.com/eks/latest/userguide/access-entries.html).

See the [Kubernetes module overview](index.md) for the ingestion and cleanup
behavior when these permissions or CRDs are absent.

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
# Secrets (optional): omit if you don't want to grant cluster-wide read access
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
    - networkpolicies
  verbs: ["list"]
# Gateway API resources (optional): only useful when the Gateway API CRDs are
# installed in the cluster. Cartography skips ingestion gracefully if the CRDs
# are absent or the verbs are not granted. See the Optional Permissions section
# above for behavior when these verbs are withheld.
- apiGroups: ["gateway.networking.k8s.io"]
  resources:
    - gateways
    - httproutes
  verbs: ["list"]
# ConfigMaps (EKS only, optional): only used to read the aws-auth ConfigMap for
# legacy IAM identity mappings. Omit if your cluster uses EKS Access Entries
# exclusively or if you don't want to grant `get` on all ConfigMaps.
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
