# Kubernetes Queries

These examples show how to inspect Kubernetes data after a successful sync.

## Inspect kubeconfig TLS posture

Use the TLS posture fields on each cluster to find kubeconfig contexts that skip
verification or lack certificate authority material:

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

## Map GPU workloads to persistent storage

Find GPU-requesting containers, their scheduled nodes, and the persistent storage
mounted by their pods:

```cypher
MATCH (container:KubernetesContainer)-[:WORKLOAD_PARENT]->(pod:KubernetesPod)
MATCH (pod)-[:RUNS_ON]->(node:KubernetesNode)
WHERE container.gpu_request > 0 OR container.gpu_limit > 0
OPTIONAL MATCH (pod)-[:MOUNTS]->(claim:KubernetesPersistentVolumeClaim)
OPTIONAL MATCH (claim)-[:BOUND_TO]->(volume:KubernetesPersistentVolume)
OPTIONAL MATCH (volume)-[:BACKED_BY]->(cloud_disk)
OPTIONAL MATCH (claim)-[:USES_STORAGE_CLASS]->(storage_class:KubernetesStorageClass)
RETURN pod.namespace, pod.name, container.name,
       container.gpu_request, container.gpu_limit,
       node.name, node.gpu_product, node.gpu_capacity,
       claim.name, volume.name, volume.csi_driver,
       labels(cloud_disk), cloud_disk.id, storage_class.name
ORDER BY pod.namespace, pod.name, container.name;
```
