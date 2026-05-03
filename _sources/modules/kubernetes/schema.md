## Kubernetes Schema

### KubernetesCluster
Representation of a [Kubernetes Cluster.](https://kubernetes.io/docs/concepts/overview/what-is-kubernetes/)

> **Ontology Mapping**: This node has the extra label `ComputeCluster` to enable cross-platform queries for compute clusters across different systems (e.g., EKSCluster, ECSCluster, AzureKubernetesCluster, GKECluster).

| Field | Description |
|-------|-------------|
| **id** | Identifier for the cluster i.e. UID of `kube-system` namespace |
| **name** | Name assigned to the cluster which is derived from kubeconfig context |
| creation\_timestamp | Timestamp of when the cluster was created i.e. creation of `kube-system` namespace |
| **external\_id** | Identifier for the cluster fetched from the kubeconfig context. For EKS clusters this should be the `arn`.|
| version | Git version of the Kubernetes cluster (e.g. v1.27.3) |
| version\_major | Major version number of the Kubernetes cluster (e.g. 1) |
| version\_minor | Minor version number of the Kubernetes cluster (e.g. 27) |
| go_version | Version of Go used to compile Kubernetes (e.g. go1.20.5) |
| compiler | Compiler used to build Kubernetes (e.g. gc) |
| platform | Operating system and architecture the cluster is running on (e.g. linux/amd64) |
| api_server_url | Kubernetes API server URL from kubeconfig |
| kubeconfig_insecure_skip_tls_verify | Whether kubeconfig is configured to skip API server TLS verification |
| kubeconfig_has_certificate_authority_data | True when kubeconfig has inline `certificate-authority-data` for this cluster |
| kubeconfig_has_certificate_authority_file | True when kubeconfig has a `certificate-authority` file path for this cluster |
| kubeconfig_ca_file_path | CA file path from kubeconfig when `certificate-authority` is configured |
| kubeconfig_has_client_certificate | True when kubeconfig user has a client cert (`client-certificate` or `client-certificate-data`) |
| kubeconfig_has_client_key | True when kubeconfig user has a client key (`client-key` or `client-key-data`) |
| kubeconfig_tls_configuration_status | Derived kubeconfig TLS posture (`valid_config`, `insecure_skip_tls`, `missing_ca_material`, `unknown`) |
| firstseen | Timestamp of when a sync job first discovered this node |
| **lastupdated** | Timestamp of the last time the node was updated |

#### Relationships
- All resources whether cluster-scoped or namespace-scoped belong to a `KubernetesCluster`.
    ```
    (:KubernetesCluster)-[:RESOURCE]->(:KubernetesNamespace,
                                       :KubernetesNode,
                                       :KubernetesPod,
                                       :KubernetesContainer,
                                       :KubernetesService,
                                       :KubernetesSecret,
                                       :KubernetesIngress,
                                       :KubernetesUser,
                                       :KubernetesGroup,
                                       :KubernetesServiceAccount,
                                       :KubernetesRole,
                                       :KubernetesRoleBinding,
                                       :KubernetesClusterRole,
                                       :KubernetesClusterRoleBinding,
                                       ...)
    (:KubernetesCluster)-[:TRUSTS]->(:KubernetesOIDCProvider)
    ```

- A `KubernetesPod` belongs to a `KubernetesCluster`
    ```
    (:KubernetesCluster)-[:RESOURCE]->(:KubernetesPod)
    ```

- A `KubernetesCluster` maps to the `EKSCluster` that hosts it when its `external_id` is an EKS cluster ARN.
    ```
    (:EKSCluster)-[:MAPS_TO]->(:KubernetesCluster)
    ```

### KubernetesNode
Representation of a [Kubernetes Node.](https://kubernetes.io/docs/concepts/architecture/nodes/)

| Field | Description |
|-------|-------------|
| **id** | Identifier for the node derived from cluster name and node name (e.g. `my-cluster/my-node`) |
| **name** | Name of the Kubernetes node |
| **cluster\_name** | Name of the Kubernetes cluster this node belongs to |
| architecture | Raw CPU architecture as reported by the node (e.g. `amd64`, `arm64`) |
| architecture\_normalized | Canonical CPU architecture after normalization (e.g. `x86_64` → `amd64`, `aarch64` → `arm64`) |
| os | Operating system of the node (e.g. `linux`) |
| os\_image | Human-readable OS image name (e.g. `Ubuntu 22.04.3 LTS`) |
| kernel\_version | Kernel version of the node (e.g. `5.15.0-1034-aws`) |
| container\_runtime\_version | Container runtime and version (e.g. `containerd://1.7.0`) |
| kubelet\_version | Version of the kubelet running on the node (e.g. `v1.27.1`) |
| firstseen | Timestamp of when a sync job first discovered this node |
| **lastupdated** | Timestamp of the last time the node was updated |

#### Relationships
- `KubernetesNode` belongs to a `KubernetesCluster`.
    ```
    (:KubernetesCluster)-[:RESOURCE]->(:KubernetesNode)
    ```

- `KubernetesPod` runs on a `KubernetesNode`.
    ```
    (:KubernetesPod)-[:RUNS_ON]->(:KubernetesNode)
    ```

### KubernetesNamespace
Representation of a [Kubernetes Namespace.](https://kubernetes.io/docs/concepts/overview/working-with-objects/namespaces/)

> **Ontology Mapping**: This node has the extra label `ComputeNamespace` to enable cross-platform queries for workload-isolation scopes across different systems.

| Field | Description |
|-------|-------------|
| **id** | UID of the Kubernetes namespace |
| **name** | Name of the Kubernetes namespace |
| creation\_timestamp | Timestamp of the creation time of the Kubernetes namespace |
| deletion\_timestamp | Timestamp of the deletion time of the Kubernetes namespace |
| status\_phase | The phase of a Kubernetes namespace indicates whether it is active, terminating, or terminated |
| **cluster\_name** | The name of the Kubernetes cluster this namespace belongs to |
| firstseen | Timestamp of when a sync job first discovered this node |
| **lastupdated** | Timestamp of the last time the node was updated |

#### Relationships
- All namespace-scoped resources belong to a `KubernetesNamespace`.
    ```
    (:KubernetesNamespace)-[:CONTAINS]->(:KubernetesPod,
                                         :KubernetesContainer,
                                         :KubernetesService,
                                         :KubernetesSecret,
                                         :KubernetesIngress,
                                         :KubernetesServiceAccount,
                                         :KubernetesRole,
                                         :KubernetesRoleBinding,
                                         ...)
    ```

- `KubernetesNamespace` points at its parent `KubernetesCluster` via the unified workload chain.
    ```
    (:KubernetesNamespace)-[:WORKLOAD_PARENT]->(:KubernetesCluster)
    ```


### KubernetesPod
Representation of a [Kubernetes Pod.](https://kubernetes.io/docs/concepts/workloads/pods/)

> **Ontology Mapping**: This node has the extra label `ComputePod` to enable cross-platform queries for the smallest schedulable workload unit across different systems (e.g., ECSTask, AzureGroupContainer).

| Field | Description |
|-------|-------------|
| **id** | UID of the Kubernetes pod |
| **name** | Name of the Kubernetes pod |
| status\_phase | The phase of a Pod is a simple, high-level summary of where the Pod is in its lifecycle. |
| creation\_timestamp | Timestamp of the creation time of the Kubernetes pod |
| deletion\_timestamp | Timestamp of the deletion time of the Kubernetes pod |
| **namespace** | The Kubernetes namespace where this pod is deployed |
| service\_account\_name | Name of the ServiceAccount used by the pod. Derived from `pod.spec.service_account_name` and defaults to `default` when unset. |
| labels | Labels are key-value pairs contained in the `PodSpec` and fetched from `pod.metadata.labels`. Stored as a JSON-encoded string. |
| **cluster\_name** | Name of the Kubernetes cluster where this pod is deployed |
| node | Name of the Kubernetes node where this pod is currently scheduled and running. Fetched from `pod.spec.node_name`. |
| architecture\_normalized | Canonical CPU architecture derived from the scheduled node when available (e.g. `amd64`, `arm64`). |
| exposed\_internet | Set by analysis job. `true` if this pod is reachable from an internet-facing load balancer. |
| exposed\_internet\_type | Set by analysis job. List of exposure types (e.g. `['lb']`). |
| firstseen | Timestamp of when a sync job first discovered this node |
| **lastupdated** | Timestamp of the last time the node was updated |

#### Relationships
- `KubernetesPod` uses a `KubernetesServiceAccount`.
    ```
    (:KubernetesPod)-[:USES_SERVICE_ACCOUNT]->(:KubernetesServiceAccount)
    ```

- `KubernetesPod` has `KubernetesContainer`. (DEPRECATED: replaced by `WORKLOAD_PARENT`, will be removed in v1.0.0)
    ```
    (:KubernetesPod)-[:CONTAINS]->(:KubernetesContainer)
    ```

- A `KubernetesNamespace` contains a `KubernetesPod`. (DEPRECATED: replaced by `WORKLOAD_PARENT`, will be removed in v1.0.0)
    ```
    (:KubernetesNamespace)-[:CONTAINS]->(:KubernetesPod)
    ```

- `KubernetesPod` points at its parent `KubernetesNamespace` via the unified workload chain.
    ```
    (:KubernetesPod)-[:WORKLOAD_PARENT]->(:KubernetesNamespace)
    ```

- `KubernetesPod` runs on a `KubernetesNode`. Not created for unscheduled pods.
    ```
    (:KubernetesPod)-[:RUNS_ON]->(:KubernetesNode)
    ```

- An internet-facing `AWSLoadBalancerV2` exposes a `KubernetesPod`. Created by the `k8s_lb_exposure` analysis job.
    ```
    (:AWSLoadBalancerV2)-[:EXPOSE {exposure_type: 'via_lb_only'}]->(:KubernetesPod)
    ```

### KubernetesContainer
Representation of a [Kubernetes Container.](https://kubernetes.io/docs/concepts/workloads/pods/#how-pods-manage-multiple-containers)

> **Ontology Mapping**: This node has the extra label `Container` to enable cross-platform queries for containers across different systems (e.g., ECSContainer, AzureContainerInstance).

| Field | Description |
|-------|-------------|
| **id** | Identifier for the container which is derived from the UID of pod and the name of container |
| **name** | Name of the container in kubernetes pod |
| **image** | Docker image used in the container |
| **namespace** | The Kubernetes namespace where this container is deployed |
| **cluster\_name** | Name of the Kubernetes cluster where this container is deployed |
| image\_pull_policy | The policy that determines when the kubelet attempts to pull the specified image (Always, Never, IfNotPresent) |
| status\_image\_id | Runtime-reported image identifier for the container. This may differ from the declared `image` field because the container runtime can rewrite tags or parent image indexes to digest-qualified references. |
| **status\_image\_sha** | The SHA portion of the runtime-reported `status_image_id` when Cartography can extract it. |
| status\_ready | Specifies whether the container has passed its readiness probe. |
| status\_started | Specifies whether the container has passed its startup probe. |
| **status\_state** | State of the container (running, terminated, waiting) |
| memory\_request | Minimum amount of memory guaranteed to be available to the container (e.g. "128Mi", "1Gi") |
| cpu\_request | Minimum amount of CPU guaranteed to be available to the container (e.g. "100m", "1") |
| memory\_limit | Maximum amount of memory the container is allowed to use (e.g. "256Mi", "2Gi") |
| cpu\_limit | Maximum amount of CPU the container is allowed to use (e.g. "500m", "2") |
| architecture\_normalized | Canonical CPU architecture derived from the scheduled node when available (e.g. `amd64`, `arm64`). |
| exposed\_internet | Set by analysis job. `true` if this container is reachable from an internet-facing load balancer. |
| exposed\_internet\_type | Set by analysis job. List of exposure types (e.g. `['lb']`). |
| firstseen | Timestamp of when a sync job first discovered this node |
| **lastupdated** | Timestamp of the last time the node was updated |


#### Relationships
- `KubernetesPod` has `KubernetesContainer`. (DEPRECATED: replaced by `WORKLOAD_PARENT`, will be removed in v1.0.0)
    ```
    (:KubernetesPod)-[:CONTAINS]->(:KubernetesContainer)
    ```

- `KubernetesContainer` points at its parent `KubernetesPod` via the unified workload chain.
    ```
    (:KubernetesContainer)-[:WORKLOAD_PARENT]->(:KubernetesPod)
    ```

- `KubernetesContainer` references container images from registries.
  `HAS_IMAGE` matches the runtime digest (`status_image_sha`) reported in container status.
  That means the relationship can point at either a top-level image artifact or a platform-specific manifest, depending on which registry node type has the matching digest.
  Runtime fields like `status_image_id` and `status_image_sha` remain on the container for later exact-image resolution work.
    ```
    (:KubernetesContainer)-[:HAS_IMAGE]->(:ECRImage)
    (:KubernetesContainer)-[:HAS_IMAGE]->(:GitLabContainerImage)
    (:KubernetesContainer)-[:HAS_IMAGE]->(:GCPArtifactRegistryContainerImage)
    (:KubernetesContainer)-[:HAS_IMAGE]->(:GCPArtifactRegistryPlatformImage)
    ```

- An internet-facing `AWSLoadBalancerV2` exposes a `KubernetesContainer`. Created by the `k8s_lb_exposure` analysis job.
    ```
    (:AWSLoadBalancerV2)-[:EXPOSE {exposure_type: 'via_lb_only'}]->(:KubernetesContainer)
    ```

### KubernetesService
Representation of a [Kubernetes Service.](https://kubernetes.io/docs/concepts/services-networking/service/)

| Field | Description |
|-------|-------------|
| **id** | UID of the kubernetes service |
| **name** | Name of the kubernetes service |
| **qualified\_name** | `<namespace>/<name>` identifier used to match the service from cross-namespace references such as `HTTPRoute.spec.rules[].backendRefs` |
| creation\_timestamp | Timestamp of the creation time of the kubernetes service |
| deletion\_timestamp | Timestamp of the deletion time of the kubernetes service |
| **namespace** | The Kubernetes namespace where this service is deployed |
| selector | Labels used by the service to select pods. Fetched from `service.spec.selector`. Stored as a JSON-encoded string. |
| type | Type of kubernetes service e.g. `ClusterIP` |
| cluster\_ip | The internal IP address assigned to the Kubernetes service within the cluster |
| load\_balancer\_ip | IP of the load balancer when service type is `LoadBalancer` |
| load\_balancer\_ingress | The list of load balancer ingress points, typically containing the hostname and IP. Stored as a JSON-encoded string. |
| **cluster\_name** | Name of the Kubernetes cluster where this service is deployed |
| exposed\_internet | Set by analysis job. `true` if this service is backed by an internet-facing load balancer. |
| exposed\_internet\_type | Set by analysis job. List of exposure types (e.g. `['lb']`). |
| firstseen | Timestamp of when a sync job first discovered this node |
| **lastupdated** | Timestamp of the last time the node was updated |

#### Relationships
- `KubernetesService` targets `KubernetesPod`.
    ```
    (:KubernetesService)-[:TARGETS]->(:KubernetesPod)
    ```

- `KubernetesService` of type `LoadBalancer` uses an AWS `AWSLoadBalancerV2` (NLB/ALB). The relationship is matched by DNS hostname from the Kubernetes service's `status.loadBalancer.ingress[].hostname` field to the `AWSLoadBalancerV2.dnsname` property. This allows linking EKS services to their backing AWS load balancers.
    ```
    (:KubernetesService)-[:USES_LOAD_BALANCER]->(:AWSLoadBalancerV2)
    ```

### KubernetesIngress
Representation of a [Kubernetes Ingress.](https://kubernetes.io/docs/concepts/services-networking/ingress/)

An Ingress is an API object that manages external access to services in a cluster, typically HTTP. Ingress may provide load balancing, SSL termination, and name-based virtual hosting.

| Field | Description |
|-------|-------------|
| **id** | UID of the Kubernetes Ingress |
| name | Name of the Kubernetes Ingress |
| **namespace** | The Kubernetes namespace where this Ingress is deployed |
| creation\_timestamp | Timestamp of the creation time of the Kubernetes Ingress |
| deletion\_timestamp | Timestamp of the deletion time of the Kubernetes Ingress |
| ingress\_class\_name | The name of the IngressClass cluster resource. Specifies which controller will implement the ingress (e.g. `nginx`, `alb`) |
| rules | The list of host rules used to configure the Ingress. Stored as a JSON-encoded string containing host/path routing rules |
| annotations | Annotations on the Ingress resource. Stored as a JSON-encoded string. Contains controller-specific configuration |
| default\_backend | A default backend capable of servicing requests that don't match any rule. Stored as a JSON-encoded string |
| cluster\_name | Name of the Kubernetes cluster where this Ingress is deployed |
| **ingress\_group\_name** | The ingress group name from the `alb.ingress.kubernetes.io/group.name` annotation (AWS Load Balancer Controller). Allows multiple Ingresses to share a single ALB |
| load\_balancer\_dns\_names | List of DNS hostnames from the Ingress status. Used to match to cloud load balancers (e.g., AWS ALB) |
| firstseen | Timestamp of when a sync job first discovered this node |
| **lastupdated** | Timestamp of the last time the node was updated |

#### Relationships
- `KubernetesIngress` belongs to a `KubernetesCluster`.
    ```
    (:KubernetesCluster)-[:RESOURCE]->(:KubernetesIngress)
    ```

- `KubernetesIngress` is contained in a `KubernetesNamespace`.
    ```
    (:KubernetesNamespace)-[:CONTAINS]->(:KubernetesIngress)
    ```

- `KubernetesIngress` targets `KubernetesService`. Routes traffic to backend services based on the configured rules.
    ```
    (:KubernetesIngress)-[:TARGETS]->(:KubernetesService)
    ```

- `KubernetesIngress` uses an `AWSLoadBalancerV2`. Matched by the DNS hostname from the Ingress status to the load balancer's DNS name.
    ```
    (:KubernetesIngress)-[:USES_LOAD_BALANCER]->(:AWSLoadBalancerV2)
    ```

### KubernetesGateway
Representation of a [Gateway API Gateway.](https://gateway-api.sigs.k8s.io/api-types/gateway/) Sourced from `gateway.networking.k8s.io/v1`. Only ingested when the Gateway API CRDs are installed in the cluster.

| Field | Description |
|-------|-------------|
| **id** | UID of the Gateway |
| **name** | Name of the Gateway |
| **namespace** | The Kubernetes namespace where this Gateway is deployed |
| **qualified\_name** | `<namespace>/<name>` identifier used to match the Gateway from `HTTPRoute.spec.parentRefs` |
| gateway\_class\_name | Name of the `GatewayClass` referenced by `spec.gatewayClassName` |
| creation\_timestamp | Epoch seconds of `metadata.creationTimestamp` |
| deletion\_timestamp | Epoch seconds of `metadata.deletionTimestamp` |
| **cluster\_name** | Name of the Kubernetes cluster where this Gateway is deployed |
| firstseen | Timestamp of when a sync job first discovered this node |
| **lastupdated** | Timestamp of the last time the node was updated |

#### Relationships
- `KubernetesGateway` belongs to a `KubernetesCluster`.
    ```
    (:KubernetesCluster)-[:RESOURCE]->(:KubernetesGateway)
    ```

- `KubernetesGateway` is contained in a `KubernetesNamespace`.
    ```
    (:KubernetesNamespace)-[:CONTAINS]->(:KubernetesGateway)
    ```

- `KubernetesGateway` routes traffic to `KubernetesHTTPRoute` resources whose `spec.parentRefs` reference it. Cross-namespace references are honored via the route's `parentRefs[].namespace` field.
    ```
    (:KubernetesGateway)-[:ROUTES]->(:KubernetesHTTPRoute)
    ```

### KubernetesHTTPRoute
Representation of a [Gateway API HTTPRoute.](https://gateway-api.sigs.k8s.io/api-types/httproute/) Sourced from `gateway.networking.k8s.io/v1`. Only ingested when the Gateway API CRDs are installed in the cluster.

| Field | Description |
|-------|-------------|
| **id** | UID of the HTTPRoute |
| **name** | Name of the HTTPRoute |
| **namespace** | The Kubernetes namespace where this HTTPRoute is deployed |
| **qualified\_name** | `<namespace>/<name>` identifier used to match this HTTPRoute from `Gateway` parents |
| hostnames | List of hostnames from `spec.hostnames` |
| creation\_timestamp | Epoch seconds of `metadata.creationTimestamp` |
| deletion\_timestamp | Epoch seconds of `metadata.deletionTimestamp` |
| **cluster\_name** | Name of the Kubernetes cluster where this HTTPRoute is deployed |
| firstseen | Timestamp of when a sync job first discovered this node |
| **lastupdated** | Timestamp of the last time the node was updated |

#### Relationships
- `KubernetesHTTPRoute` belongs to a `KubernetesCluster`.
    ```
    (:KubernetesCluster)-[:RESOURCE]->(:KubernetesHTTPRoute)
    ```

- `KubernetesHTTPRoute` is contained in a `KubernetesNamespace`.
    ```
    (:KubernetesNamespace)-[:CONTAINS]->(:KubernetesHTTPRoute)
    ```

- `KubernetesHTTPRoute` targets `KubernetesService` resources via `spec.rules[].backendRefs`. Only refs whose group/kind resolve to the core `Service` type are considered.
    ```
    (:KubernetesHTTPRoute)-[:TARGETS]->(:KubernetesService)
    ```

### KubernetesSecret
Representation of a [Kubernetes Secret.](https://kubernetes.io/docs/concepts/configuration/secret/)

> **Ontology Mapping**: This node has the extra label `Secret` and normalized `_ont_*` properties for cross-platform secret queries. See [Secret](../../ontology/schema.md#secret).

| Field | Description |
|-------|-------------|
| **id** | UID of the kubernetes secret |
| **name** | Name of the kubernetes secret |
| creation\_timestamp | Timestamp of the creation time of the kubernetes secret |
| deletion\_timestamp | Timestamp of the deletion time of the kubernetes secret |
| **namespace** | The Kubernetes namespace where this secret is deployed |
| owner\_references | References to objects that own this secret. Useful if a secret is an `ExternalSecret`. Fetched from `secret.metadata.owner_references`. Stored as a JSON-encoded string |
| type | Type of kubernetes secret (e.g. `Opaque`) |
| **cluster\_name** | Name of the Kubernetes cluster where this secret is deployed |
| firstseen | Timestamp of when a sync job first discovered this node |
| **lastupdated** | Timestamp of the last time the node was updated |

#### Relationships
- `KubernetesNamespace` has `KubernetesSecret`.
    ```
    (:KubernetesNamespace)-[:CONTAINS]->(:KubernetesSecret)
    ```

### KubernetesServiceAccount
Representation of a [Kubernetes ServiceAccount.](https://kubernetes.io/docs/concepts/security/service-accounts/)

> **Ontology Mapping**: This node has the extra label `ServiceAccount` to enable cross-platform queries for service accounts across different systems (e.g., GCPServiceAccount, OpenAIServiceAccount, ScalewayApplication).

| Field | Description |
|-------|-------------|
| **id** | Identifier for the ServiceAccount derived from cluster_name, namespace and name (e.g. `my-cluster/default/my-service-account`) |
| name | Name of the Kubernetes ServiceAccount |
| namespace | The Kubernetes namespace where this ServiceAccount is deployed |
| aws_role_arn | ARN from the IRSA annotation `eks.amazonaws.com/role-arn`, when present. Used to link the ServiceAccount to an `AWSRole`. |
| gcp\_service\_account | Email from the GKE Workload Identity annotation `iam.gke.io/gcp-service-account`, when present. Used to link the ServiceAccount to a `GCPServiceAccount`. |
| uid | UID of the Kubernetes ServiceAccount |
| creation\_timestamp | Timestamp of the creation time of the Kubernetes ServiceAccount |
| resource\_version | The resource version of the ServiceAccount for optimistic concurrency control |
| automount\_service\_account\_token | Whether the ServiceAccount token should be automatically mounted in pods |
| firstseen | Timestamp of when a sync job first discovered this node |
| **lastupdated** | Timestamp of the last time the node was updated |

#### Relationships
- `KubernetesServiceAccount` belongs to a `KubernetesCluster`.
    ```
    (:KubernetesCluster)-[:RESOURCE]->(:KubernetesServiceAccount)
    ```

- `KubernetesServiceAccount` is contained in a `KubernetesNamespace`.
    ```
    (:KubernetesNamespace)-[:CONTAINS]->(:KubernetesServiceAccount)
    ```

- `KubernetesServiceAccount` is used by a `KubernetesPod`.
    ```
    (:KubernetesPod)-[:USES_SERVICE_ACCOUNT]->(:KubernetesServiceAccount)
    ```

- `KubernetesServiceAccount` can assume an `AWSRole` via IRSA when annotated with `eks.amazonaws.com/role-arn`.
    ```
    (:KubernetesServiceAccount)-[:ASSUMES_ROLE]->(:AWSRole)
    ```

- `KubernetesServiceAccount` impersonates a `GCPServiceAccount` via GKE Workload Identity when annotated with `iam.gke.io/gcp-service-account`.
    ```
    (:KubernetesServiceAccount)-[:WORKLOAD_IDENTITY_BINDING]->(:GCPServiceAccount)
    ```

- `KubernetesServiceAccount` is used as a subject in `KubernetesRoleBinding`.
    ```
    (:KubernetesRoleBinding)-[:SUBJECT]->(:KubernetesServiceAccount)
    ```

- `KubernetesServiceAccount` is used as a subject in `KubernetesClusterRoleBinding`.
    ```
    (:KubernetesClusterRoleBinding)-[:SUBJECT]->(:KubernetesServiceAccount)
    ```

### KubernetesUser
Representation of a Kubernetes [User](https://kubernetes.io/docs/reference/access-authn-authz/authentication/) identity in K8s RBAC.

> **Ontology Mapping**: This node has the extra label `UserAccount` to enable cross-platform queries for user accounts across different systems (e.g., OktaUser, EntraUser, GSuiteUser).

| Field | Description |
|-------|-------------|
| **id** | Identifier for the user |
| name | Name of the Kubernetes user |
| cluster\_name | Name of the cluster this user belongs to |
| firstseen | Timestamp of when a sync job first discovered this node |
| **lastupdated** | Timestamp of the last time the node was updated |

#### Relationships
- `KubernetesUser` belongs to a `KubernetesCluster`.
    ```
    (:KubernetesCluster)-[:RESOURCE]->(:KubernetesUser)
    ```

- `KubernetesUser` can map to an `OktaUser`.
    ```
    (:OktaUser)-[:MAPS_TO]->(:KubernetesUser)
    ```

- `KubernetesUser` can map to an `AWSRole`.
    ```
    (:AWSRole)-[:MAPS_TO]->(:KubernetesUser)
    ```

- `KubernetesUser` can map to an `AWSUser`.
    ```
    (:AWSUser)-[:MAPS_TO]->(:KubernetesUser)
    ```

### KubernetesGroup
Representation of a Kubernetes [Group](https://kubernetes.io/docs/reference/access-authn-authz/rbac/) in K8s RBAC.

> **Ontology Mapping**: This node has the extra label `UserGroup` to enable cross-platform queries for user groups across different systems (e.g., OktaGroup, EntraGroup, AWSGroup).

| Field | Description |
|-------|-------------|
| **id** | Identifier for the group |
| name | Name of the Kubernetes group |
| cluster\_name | Name of the cluster this group belongs to |
| firstseen | Timestamp of when a sync job first discovered this node |
| **lastupdated** | Timestamp of the last time the node was updated |

#### Relationships
- `KubernetesGroup` belongs to a `KubernetesCluster`.
    ```
    (:KubernetesCluster)-[:RESOURCE]->(:KubernetesGroup)
    ```

- `KubernetesGroup` can map to an `OktaGroup`.
    ```
    (:OktaGroup)-[:MAPS_TO]->(:KubernetesGroup)
    ```

- `KubernetesGroup` can map to an `AWSRole`.
    ```
    (:AWSRole)-[:MAPS_TO]->(:KubernetesGroup)
    ```

- `KubernetesGroup` can map to an `AWSUser`.
    ```
    (:AWSUser)-[:MAPS_TO]->(:KubernetesGroup)
    ```

### KubernetesRole
Representation of a [Kubernetes Role.](https://kubernetes.io/docs/reference/access-authn-authz/rbac/#role-and-clusterrole)

> **Ontology Mapping**: This node has the extra label `PermissionRole` to enable cross-platform queries for IAM roles and permission roles across different systems (e.g., AWSRole, AzureRoleDefinition, GCPRole, KubernetesRole).

| Field | Description |
|-------|-------------|
| **id** | Identifier for the Role derived from cluster_name, namespace and name (e.g. `my-cluster/default/pod-reader`) |
| name | Name of the Kubernetes Role |
| namespace | The Kubernetes namespace where this Role is deployed |
| uid | UID of the Kubernetes Role |
| creation\_timestamp | Timestamp of the creation time of the Kubernetes Role |
| resource\_version | The resource version of the Role for optimistic concurrency control |
| api\_groups | List of API groups that this Role grants access to (e.g. `["core", "apps"]`) |
| resources | List of resources that this Role grants access to (e.g. `["pods", "services"]`) |
| verbs | List of verbs/actions that this Role allows (e.g. `["get", "list", "create"]`) |
| cluster\_name | Name of the Kubernetes cluster where this Role is deployed |
| firstseen | Timestamp of when a sync job first discovered this node |
| **lastupdated** | Timestamp of the last time the node was updated |

#### Relationships
- `KubernetesRole` belongs to a `KubernetesCluster`.
    ```
    (:KubernetesCluster)-[:RESOURCE]->(:KubernetesRole)
    ```

- `KubernetesRole` is contained in a `KubernetesNamespace`.
    ```
    (:KubernetesNamespace)-[:CONTAINS]->(:KubernetesRole)
    ```

- `KubernetesRole` is referenced by `KubernetesRoleBinding`.
    ```
    (:KubernetesRoleBinding)-[:ROLE_REF]->(:KubernetesRole)
    ```

### KubernetesRoleBinding
Representation of a [Kubernetes RoleBinding.](https://kubernetes.io/docs/reference/access-authn-authz/rbac/#rolebinding-and-clusterrolebinding)

| Field | Description |
|-------|-------------|
| **id** | Identifier for the RoleBinding derived from cluster_name, namespace and name (e.g. `my-cluster/default/my-binding`) |
| name | Name of the Kubernetes RoleBinding |
| namespace | The Kubernetes namespace where this RoleBinding is deployed |
| uid | UID of the Kubernetes RoleBinding |
| creation\_timestamp | Timestamp of the creation time of the Kubernetes RoleBinding |
| resource\_version | The resource version of the RoleBinding for optimistic concurrency control |
| role\_name | Name of the Role that this RoleBinding references |
| role\_kind | Kind of the role reference (e.g. `Role` or `ClusterRole`) |
| subject\_name | Name of the subject (ServiceAccount, User, or Group) |
| subject\_namespace | Namespace of the subject (for ServiceAccounts) |
| subject\_service\_account\_id | Identifier for the target ServiceAccount (used for relationship matching) |
| role\_id | Identifier for the target Role (used for relationship matching) |
| cluster\_name | Name of the Kubernetes cluster where this RoleBinding is deployed |
| firstseen | Timestamp of when a sync job first discovered this node |
| **lastupdated** | Timestamp of the last time the node was updated |

#### Relationships
- `KubernetesRoleBinding` belongs to a `KubernetesCluster`.
    ```
    (:KubernetesCluster)-[:RESOURCE]->(:KubernetesRoleBinding)
    ```

- `KubernetesRoleBinding` is contained in a `KubernetesNamespace`.
    ```
    (:KubernetesNamespace)-[:CONTAINS]->(:KubernetesRoleBinding)
    ```

- `KubernetesRoleBinding` binds a subject to a role.
    ```
    (:KubernetesRoleBinding)-[:SUBJECT]->(:KubernetesServiceAccount)
    (:KubernetesRoleBinding)-[:ROLE_REF]->(:KubernetesRole)
    ```

### KubernetesClusterRole
Representation of a [Kubernetes ClusterRole.](https://kubernetes.io/docs/reference/access-authn-authz/rbac/#role-and-clusterrole)

> **Ontology Mapping**: This node has the extra label `PermissionRole` to enable cross-platform queries for IAM roles and permission roles across different systems (e.g., AWSRole, AzureRoleDefinition, GCPRole, KubernetesRole).

| Field | Description |
|-------|-------------|
| **id** | Identifier for the ClusterRole derived from cluster_name and name (e.g. `my-cluster/cluster-admin`) |
| name | Name of the Kubernetes ClusterRole |
| uid | UID of the Kubernetes ClusterRole |
| creation\_timestamp | Timestamp of the creation time of the Kubernetes ClusterRole |
| resource\_version | The resource version of the ClusterRole for optimistic concurrency control |
| api\_groups | List of API groups that this ClusterRole grants access to (e.g. `["core", "apps"]`) |
| resources | List of resources that this ClusterRole grants access to (e.g. `["pods", "services"]`) |
| verbs | List of verbs/actions that this ClusterRole allows (e.g. `["get", "list", "create"]`) |
| firstseen | Timestamp of when a sync job first discovered this node |
| **lastupdated** | Timestamp of the last time the node was updated |

#### Relationships
- `KubernetesClusterRole` belongs to a `KubernetesCluster`.
    ```
    (:KubernetesCluster)-[:RESOURCE]->(:KubernetesClusterRole)
    ```

- `KubernetesClusterRole` is referenced by `KubernetesClusterRoleBinding`.
    ```
    (:KubernetesClusterRoleBinding)-[:ROLE_REF]->(:KubernetesClusterRole)
    ```

### KubernetesClusterRoleBinding
Representation of a [Kubernetes ClusterRoleBinding.](https://kubernetes.io/docs/reference/access-authn-authz/rbac/#rolebinding-and-clusterrolebinding)

| Field | Description |
|-------|-------------|
| **id** | Identifier for the ClusterRoleBinding derived from cluster_name and name (e.g. `my-cluster/cluster-admin-binding`) |
| name | Name of the Kubernetes ClusterRoleBinding |
| namespace | The namespace of the subject (for cross-namespace subject references) |
| uid | UID of the Kubernetes ClusterRoleBinding |
| creation\_timestamp | Timestamp of the creation time of the Kubernetes ClusterRoleBinding |
| resource\_version | The resource version of the ClusterRoleBinding for optimistic concurrency control |
| role\_name | Name of the ClusterRole that this ClusterRoleBinding references |
| role\_kind | Kind of the role reference (typically `ClusterRole`) |
| subject\_name | Name of the subject (ServiceAccount, User, or Group) |
| subject\_namespace | Namespace of the subject (for ServiceAccounts) |
| subject\_service\_account\_id | Identifier for the target ServiceAccount (used for relationship matching) |
| role\_id | Identifier for the target ClusterRole (used for relationship matching) |
| firstseen | Timestamp of when a sync job first discovered this node |
| **lastupdated** | Timestamp of the last time the node was updated |

#### Relationships
- `KubernetesClusterRoleBinding` belongs to a `KubernetesCluster`.
    ```
    (:KubernetesCluster)-[:RESOURCE]->(:KubernetesClusterRoleBinding)
    ```

- `KubernetesClusterRoleBinding` binds a subject to a cluster role.
    ```
    (:KubernetesClusterRoleBinding)-[:SUBJECT]->(:KubernetesServiceAccount)
    (:KubernetesClusterRoleBinding)-[:ROLE_REF]->(:KubernetesClusterRole)
    ```

### KubernetesOIDCProvider
Representation of an external OIDC identity provider for a Kubernetes cluster. This node contains the configuration details of how the cluster is set up to trust external identity systems (such as Auth0, Okta, Entra). The ingestion of users/groups from the identity provider is handled by the respective identity provider Cartography module. Then the Kubernetes module creates relationships between those identities and KubernetesUsers and KubernetesGroups.

| Field | Description |
|-------|-------------|
| **id** | Identifier for the OIDC Provider derived from cluster name and provider name (e.g. `my-cluster/oidc/auth0-provider`) |
| issuer_url | URL of the OIDC issuer (e.g. `https://company.auth0.com/`) |
| cluster_name | Name of the Kubernetes cluster this provider is associated with |
| k8s_platform | Type of Kubernetes platform managing this OIDC configuration (e.g. `eks` for AWS EKS, `aks` for Azure AKS) |
| client_id | OIDC client ID used for authentication |
| status | Status of the OIDC provider configuration (e.g. `ACTIVE`) |
| name | Name of the OIDC provider configuration |
| arn | AWS ARN of the identity provider configuration (for EKS) |
| firstseen | Timestamp of when a sync job first discovered this node |
| **lastupdated** | Timestamp of the last time the node was updated |

#### Relationships
- `KubernetesOIDCProvider` is trusted by a `KubernetesCluster`.
    ```
    (:KubernetesCluster)-[:TRUSTS]->(:KubernetesOIDCProvider)
    ```

Note: Identity mapping between external OIDC providers (Okta, Auth0, etc.) and Kubernetes users/groups is handled through direct relationships from the external identity provider nodes to Kubernetes nodes, not through the `KubernetesOIDCProvider` metadata node.
