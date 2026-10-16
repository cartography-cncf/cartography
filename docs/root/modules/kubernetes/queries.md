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
mounted or exposed as a raw block device to those containers:

```cypher
MATCH (container:KubernetesContainer)-[:WORKLOAD_PARENT]->(pod:KubernetesPod)
MATCH (pod)-[:RUNS_ON]->(node:KubernetesNode)
WHERE container.gpu_request > 0 OR container.gpu_limit > 0
OPTIONAL MATCH (container)
  -[storage_access:MOUNTS|USES_BLOCK_DEVICE]->
  (claim:KubernetesPersistentVolumeClaim)
OPTIONAL MATCH (claim)-[:BOUND_TO]->(volume:KubernetesPersistentVolume)
OPTIONAL MATCH (volume)-[:BACKED_BY]->(cloud_disk)
OPTIONAL MATCH (claim)-[:USES_STORAGE_CLASS]->(storage_class:KubernetesStorageClass)
RETURN pod.namespace, pod.name, container.name,
       container.gpu_request, container.gpu_limit,
       node.name, node.gpu_product, node.gpu_capacity,
       type(storage_access), claim.name,
       CASE type(storage_access)
         WHEN 'MOUNTS' THEN
           claim.id IN coalesce(container.persistent_volume_claim_read_write_ids, [])
         ELSE null
       END AS read_write,
       volume.name, volume.csi_driver,
       labels(cloud_disk), cloud_disk.id, storage_class.name
ORDER BY pod.namespace, pod.name, container.name;
```

## GKE workload access to Google Cloud

IAM allow bindings that grant something to a pod's Kubernetes service account through
Workload Identity Federation for GKE. IAM conditions are not evaluated.

```cypher
MATCH (pod:KubernetesPod)-[:RUNS_AS]->(ksa:KubernetesServiceAccount)
      -[grant:HAS_ALLOW_POLICY]->(binding:GCPPolicyBinding)
OPTIONAL MATCH (binding)-[:APPLIES_TO]->(resource)
RETURN pod.name, ksa.namespace, ksa.name, binding.role, grant.matched_members,
       binding.condition_expression, labels(resource), resource.id
```

Annotated service accounts with no verified impersonation grant in the graph. Missing
IAM policy inventory produces the same result, so check GCP policy-binding coverage
before treating these as misconfigured:

```cypher
MATCH (ksa:KubernetesServiceAccount)-[:ANNOTATED_SERVICE_ACCOUNT]->(gsa:GCPServiceAccount)
WHERE NOT (ksa)-[:WORKLOAD_IDENTITY_BINDING]->(gsa)
RETURN ksa.namespace, ksa.name, gsa.email
```

What the impersonated Google service account is granted:

```cypher
MATCH (pod:KubernetesPod)-[:RUNS_AS]->(ksa:KubernetesServiceAccount)
      -[:WORKLOAD_IDENTITY_BINDING]->(gsa:GCPServiceAccount)
      -[:HAS_ALLOW_POLICY]->(binding:GCPPolicyBinding)
RETURN pod.name, ksa.name, gsa.email, binding.role, binding.resource
```

## GKE load balancer paths

From a GCP forwarding rule through a Gateway to the pods and their identities:

```cypher
MATCH (lb:GCPForwardingRule)<-[:USES_LOAD_BALANCER]-(gw:KubernetesGateway)
      -[:ROUTES]->(:KubernetesHTTPRoute)-[:TARGETS]->(:KubernetesService)
      -[:TARGETS]->(pod:KubernetesPod)-[:RUNS_AS]->(ksa:KubernetesServiceAccount)
RETURN lb.name, lb.load_balancing_scheme, gw.name, pod.name, ksa.name
```

## GKE node credentials

```cypher
MATCH (cloud:GKECluster)-[:MAPS_TO]->(:KubernetesCluster)
      -[:RESOURCE]->(node:KubernetesNode)-[:MEMBER_OF]->(pool:GKENodePool)
OPTIONAL MATCH (pool)-[:RUNS_AS]->(account:GCPServiceAccount)
RETURN cloud.name, cloud.autopilot_enabled, node.name,
       pool.workload_metadata_mode, pool.oauth_scopes, account.email
```

Node pools in `GCE_METADATA` mode expose the node service account to pods.
