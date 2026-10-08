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

Show IAM allow bindings whose full member selector matches a workload's Kubernetes
ServiceAccount. Conditions remain on the policy node and require separate evaluation.

```cypher
MATCH (pod:KubernetesPod)-[:RUNS_AS]->(ksa:KubernetesServiceAccount)
      -[grant:HAS_ALLOW_POLICY]->(binding:GCPPolicyBinding)
OPTIONAL MATCH (binding)-[:APPLIES_TO]->(resource)
RETURN pod.name, ksa.namespace, ksa.name, binding.role,
       grant.matched_members, binding.condition_expression,
       grant.policy_lastupdated, labels(resource), resource.id
```

Find annotations with no verified unconditional impersonation grant in the current
graph. Missing IAM inventory also produces this result; check collection coverage.

```cypher
MATCH (ksa:KubernetesServiceAccount)-[:ANNOTATED_SERVICE_ACCOUNT]->(gsa:GCPServiceAccount)
WHERE NOT (ksa)-[:WORKLOAD_IDENTITY_BINDING]->(gsa)
RETURN ksa.namespace, ksa.name, gsa.email, ksa.lastupdated
```

Follow verified impersonation configuration to the Google identity's policy bindings:

```cypher
MATCH (pod:KubernetesPod)-[:RUNS_AS]->(ksa:KubernetesServiceAccount)
      -[:WORKLOAD_IDENTITY_BINDING]->(gsa:GCPServiceAccount)
MATCH (principal:GCPPrincipal {email: gsa.email})-[:HAS_ALLOW_POLICY]->(binding:GCPPolicyBinding)
RETURN pod.name, ksa.name, gsa.email, binding.role, binding.condition_expression
```

## GKE load balancer paths

Show forwarding rules correlated with Services, Ingresses, and Gateways. An internal
forwarding rule is not internet exposure; external scheme alone does not prove
backend health or firewall reachability.

```cypher
MATCH (entry)-[:USES_LOAD_BALANCER]->(lb:GCPForwardingRule)
RETURN labels(entry), entry.namespace, entry.name,
       lb.name, lb.ip_address, lb.load_balancing_scheme, lb.network
```

Follow a Gateway through an accepted HTTPRoute to workloads and their cloud identities:

```cypher
MATCH (lb:GCPForwardingRule)<-[:USES_LOAD_BALANCER]-(gw:KubernetesGateway)
      -[:ROUTES]->(:KubernetesHTTPRoute)-[:TARGETS]->(:KubernetesService)
      -[:TARGETS]->(pod:KubernetesPod)-[:RUNS_AS]->(ksa:KubernetesServiceAccount)
RETURN lb.name, lb.load_balancing_scheme, gw.name, pod.name, ksa.name
```

## GKE node credential configuration

```cypher
MATCH (cloud:GKECluster)-[:MAPS_TO]->(cluster:KubernetesCluster)
      -[:RESOURCE]->(node:KubernetesNode)-[:MEMBER_OF]->(pool:GKENodePool)
OPTIONAL MATCH (pool)-[:RUNS_AS]->(account:GCPServiceAccount)
RETURN cloud.name, cloud.autopilot_enabled, node.name,
       pool.workload_metadata_mode, pool.oauth_scopes, account.email
```

`GCE_METADATA` and `GKE_METADATA` distinguish node metadata modes. This query describes
node configuration, not whether every pod can obtain those node credentials; host
networking and GKE version-specific behavior also matter.
