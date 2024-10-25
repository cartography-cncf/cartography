## Kubernetes Configuration

.. _kubernetes_config:

Follow these steps to analyze Kubernetes objects in Cartography.

1. Configure a [kubeconfig file](https://kubernetes.io/docs/concepts/configuration/organize-cluster-access-kubeconfig/) specifying access to one or mulitple clusters.
    - Access to mutliple K8 clusters can be organized in a single kubeconfig file. Intel module of Kubernetes will automatically detect that and attempt to sync each cluster.
2. Note down the path of configured kubeconfig file and pass it to cartography CLI with `--k8s-kubeconfig` parameter.
