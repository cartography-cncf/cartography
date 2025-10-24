## Kubernetes Configuration

Follow these steps to analyze Kubernetes objects in Cartography.

1. Configure a [kubeconfig file](https://kubernetes.io/docs/concepts/configuration/organize-cluster-access-kubeconfig/) specifying access to one or multiple clusters.
    - Access to multiple Kubernetes clusters can be organized in a single kubeconfig file. The Kubernetes intel module will automatically detect and attempt to sync each cluster.
2. Note the path of your configured kubeconfig file and pass it to the Cartography CLI using the `--k8s-kubeconfig` parameter.

### Amazon EKS Integration

For Kubernetes clusters managed through Amazon EKS, you can provision access using [EKS access entries](https://docs.aws.amazon.com/eks/latest/userguide/access-entries.html). Use the following command with the `--aws-eks-sync-cluster-resources` flag to enable the EKS intel module to sync cluster resources:

```
AWS_PROFILE=security-cartography AWS_DEFAULT_REGION=us-east-1 \
uv run cartography \
 --neo4j-uri bolt://localhost:7687 \
 --selected-modules aws \
 --aws-requested-syncs eks \
 --aws-eks-sync-cluster-resources
```
