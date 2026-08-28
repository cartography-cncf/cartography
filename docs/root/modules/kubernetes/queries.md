# Kubernetes Queries

These examples show how to inspect Kubernetes data after a successful sync.

## Trace internet-facing load balancers to Kubernetes workloads

Find Kubernetes traffic entry points correlated with internet-facing cloud load
balancers and the pods selected by their service backends:

```cypher
CALL {
  MATCH (service:KubernetesService)-[:USES_LOAD_BALANCER]->(load_balancer:LoadBalancer)
  WHERE load_balancer.exposed_internet = true OR (
    load_balancer._ont_source = 'aws'
    AND load_balancer._ont_scheme = 'internet_facing'
    AND load_balancer._ont_lb_type = 'network'
  )
  RETURN load_balancer, service, service AS entry_point
  UNION
  MATCH (ingress:KubernetesIngress)-[:USES_LOAD_BALANCER]->(load_balancer:LoadBalancer)
  WHERE load_balancer.exposed_internet = true OR (
    load_balancer._ont_source = 'aws'
    AND load_balancer._ont_scheme = 'internet_facing'
    AND load_balancer._ont_lb_type = 'network'
  )
  MATCH (ingress)-[:TARGETS]->(service:KubernetesService)
  RETURN load_balancer, service, ingress AS entry_point
  UNION
  MATCH (gateway:KubernetesGateway {programmed: true})
    -[:USES_LOAD_BALANCER]->(load_balancer:LoadBalancer)
  WHERE load_balancer.exposed_internet = true OR (
    load_balancer._ont_source = 'aws'
    AND load_balancer._ont_scheme = 'internet_facing'
    AND load_balancer._ont_lb_type = 'network'
  )
  MATCH (gateway)-[:ROUTES]->(route:KubernetesHTTPRoute)
    -[:TARGETS]->(service:KubernetesService)
  WHERE gateway.qualified_name IN route.accepted_parent_gateway_qualified_names
  RETURN load_balancer, service, gateway AS entry_point
}
MATCH (service:KubernetesService)-[:TARGETS]->(pod:KubernetesPod)
RETURN labels(load_balancer), load_balancer.id,
       labels(entry_point), entry_point.name,
       service.namespace, service.name, pod.name
ORDER BY service.namespace, service.name, pod.name;
```

This query reports correlated cloud load-balancer paths. Gateway paths require a
current `Programmed=True` Gateway condition and an `Accepted=True` route-parent
condition. Kubernetes status can identify a bound hostname or public IP address,
but it can't by itself prove that the endpoint is reachable from the internet.
IP correlation is an exact, graph-wide match; recycled addresses can correlate
stale Kubernetes status with an unrelated load balancer, so treat IP-only paths
as evidence to verify rather than proof of exposure.

## Inspect port-attributed container exposure

Find containers whose declared protocol and port match a current EndpointSlice
port for an internet-exposed Service:

```cypher
MATCH (service:KubernetesService {exposed_internet: true})
  <-[:FOR_SERVICE]-(slice:KubernetesEndpointSlice)
  -[:TARGETS]->(pod:KubernetesPod)-[:CONTAINS]->(container:KubernetesContainer)
WHERE slice.lastupdated = service.lastupdated
  AND any(port_key IN slice.port_keys
          WHERE port_key IN container.container_port_keys)
RETURN service.namespace, service.name, pod.name, container.name,
       [port_key IN slice.port_keys
        WHERE port_key IN container.container_port_keys] AS matching_ports
ORDER BY service.namespace, service.name, pod.name, container.name;
```

An absent result doesn't prove that a process is unreachable. Kubernetes doesn't
require containers to declare the ports on which their processes listen.

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
