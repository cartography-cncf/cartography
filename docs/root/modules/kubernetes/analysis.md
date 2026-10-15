# Kubernetes Analysis

## Pods with no modeled internet path

`exposed_internet` is only ever written as `true`. The
`k8s_no_modeled_internet_path` analysis job records the other case. At the end
of each cluster's sync, it sets `no_modeled_internet_path = true` and
`no_modeled_internet_path_checked_at` (the run's update tag) on a
`KubernetesPod` and its `KubernetesContainer` nodes when:

- the cluster was checked for unmodeled internet paths in this run, and none
  were found;
- the pod does not use the host network, and declares no host port on any of
  its containers or native sidecars (init containers with
  `restartPolicy: Always`, recorded in the pod's `host_ports`);
- no `NodePort` or `LoadBalancer` Service selects the pod. A `LoadBalancer`
  Service opens a node port on every node unless `allocateLoadBalancerNodePorts`
  is false, which the graph does not record, so it counts as a `NodePort`
  Service even behind an internal load balancer. The backends of an Ingress
  that shares its load balancer with a `LoadBalancer` Service count as selected
  by it too: that Service belongs to an in-cluster controller such as
  ingress-nginx, which routes what reaches its node port to them;
- every `AWSLoadBalancerV2` that reaches the pod through a Service or an
  Ingress, directly or chained behind another load balancer, is `internal`, its
  AWS account was checked at or after the load balancer was synced, with no
  unmodeled internet paths, and no load balancer targets one of that account's
  load balancer interfaces. See the [AWS analysis](../aws/analysis.md) page;
- neither the pod nor its containers are marked `exposed_internet`.

The property describes the graph, not the network: no internet path that
Cartography models reaches the pod. The paths it does not see are listed below.

The job only checks pods that the same run synced, so a current result has
`no_modeled_internet_path_checked_at` equal to the pod's `lastupdated`. Its
properties are replaced at the end of the run instead of being cleared first,
so a run that fails part-way leaves the previous values, with an older tag.

When the Service, Ingress or Node list fails, or listing Gateway API objects is
denied, that sync keeps the objects from its previous run instead of loading a
partial list, and the run withdraws the cluster's check, so no pod in the
cluster is marked.

A result reflects the AWS data in the graph when the cluster was synced. An AWS
sync that runs later, for example one that loads a new internet-facing load
balancer in front of the pod or a CloudFront VPC origin in the load balancer's
account, does not check the pod again. The cluster's next sync does, so run the
AWS sync before the Kubernetes sync to keep the two close.

```cypher
MATCH (cluster:KubernetesCluster)-[:RESOURCE]->(pod:KubernetesPod)
RETURN cluster.name, cluster.unmodeled_internet_paths,
       pod.namespace, pod.name, pod.exposed_internet,
       coalesce(pod.no_modeled_internet_path, false)
         AND pod.no_modeled_internet_path_checked_at >= pod.lastupdated
         AS no_modeled_internet_path
ORDER BY cluster.name, pod.namespace, pod.name;
```

## Unmodeled internet paths

The `k8s_unmodeled_internet_paths` job runs just before it and records on the
`KubernetesCluster` the paths into the cluster whose internet reach the graph
cannot resolve:

- `unmodeled_internet_paths`: up to 10 IDs. Unset when there are none.
- `unmodeled_internet_path_count`: how many it found, `0` when there are none.
- `unmodeled_internet_paths_checked_at`: the update tag of the run that checked
  the cluster.

It finds:

- Ingresses and `LoadBalancer` Services with no matching `AWSLoadBalancerV2`,
  or whose status lists a hostname that matches none, and Ingresses whose
  status lists an IP address without a hostname (`load_balancer_ips`). Each
  status address is an entry point, so one the graph cannot resolve may face
  the internet even when another is an internal load balancer, for example
  when ingress-nginx publishes several addresses with
  `--publish-status-address`. The IP addresses of a `LoadBalancer` Service are
  not checked, because the pods it selects, and the backends of an Ingress
  that shares its load balancer, are never marked;
- Services without a selector that are `NodePort` or `LoadBalancer` Services
  or that an Ingress routes to, and `ExternalName` Services that an Ingress
  routes to. The endpoints of a Service without a selector are managed by hand,
  and an `ExternalName` Service is resolved through DNS and ignores any selector
  it has, so the pods behind them are not linked to them;
- every Gateway and HTTPRoute, since Gateways are not linked to a load
  balancer;
- an `AWSLoadBalancerV2` that may face the internet, judged as for the pods
  above, and sends traffic to a private IP on an interface of the EC2
  instance behind one of the cluster's nodes. With the Amazon VPC CNI, pod IPs
  are secondary IPs on node interfaces, so an IP target group registered by a
  `TargetGroupBinding`, or by hand, can reach pods that no Service or Ingress
  links to that load balancer. The graph does not record which pod holds an IP,
  so this also counts the target groups of an Ingress or a `LoadBalancer`
  Service in IP target mode: a single internet-facing load balancer in IP
  target mode withholds every result in its cluster;
- nodes with an EC2 instance ID whose instance is not in the graph, because the
  previous check cannot see their interfaces;
- nodes whose instance has an interface with an IPv6 address, or a public IP on
  a secondary private IP. The pods of an IPv6 cluster get globally routable
  addresses from the nodes' interfaces, and with the VPC CNI an Elastic IP on a
  secondary private IP reaches the pod that holds it.

The IDs are Kubernetes UIDs for Ingresses, Services, Gateways and HTTPRoutes,
the load balancer ID (its DNS name), and the node ID. A cluster whose load
balancers are not AWS load balancers, or whose AWS account is not synced into
the same graph, gets results only when it has none of these.

## Paths the checks do not see

- `externalIPs` on Services, and routes defined by custom resources such as
  service mesh gateways.
- Pod IPs that are not secondary IPs on a node instance's interface: prefix
  delegation, security groups for pods (branch interfaces), EKS Fargate pods
  and overlay networks. A load balancer IP target on such a pod is not seen,
  and neither is an IPv6 prefix on an interface that has no IPv6 address.
- Load balancer IP targets, IPv6 addresses and public IPs on node interfaces
  when the nodes' AWS account was synced without `ec2:network_interface`,
  `ec2:subnet` or `ec2:load_balancer_v2:expose`.
- The AWS paths listed on the [AWS analysis](../aws/analysis.md) page.
- Application-layer forwarding by another workload.
