## Kubernetes Configuration

Follow these steps to analyze Kubernetes objects in Cartography.

1. Configure a [kubeconfig file](https://kubernetes.io/docs/concepts/configuration/organize-cluster-access-kubeconfig/) specifying access to one or mulitple clusters.
    - Access to mutliple K8 clusters can be organized in a single kubeconfig file. Intel module of Kubernetes will automatically detect that and attempt to sync each cluster.
2. Note down the path of configured kubeconfig file and pass it to cartography CLI with `--k8s-kubeconfig` parameter.

### Required Permissions

Cartography's Kubernetes module requires read-only access to the following resources. Create a ClusterRole and bind it to the identity used by Cartography:

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
    - pods
    - services
    - serviceaccounts
  verbs: ["list"]
# Secrets - list only, no read access
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
# ConfigMaps - read aws-auth identity mapping
- apiGroups: [""]
  resources:
    - configmaps
  verbs: ["get"]
```

The `/version` endpoint (used to detect the cluster version) requires no additional RBAC — it is accessible by default via the `system:public-info-viewer` ClusterRole.
