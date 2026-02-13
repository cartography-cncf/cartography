## Kubernetes Schema

### KubernetesCluster
Representation of a [Kubernetes Cluster.](https://kubernetes.io/docs/concepts/overview/what-is-kubernetes/)

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
| firstseen | Timestamp of when a sync job first discovered this node |
| **lastupdated** | Timestamp of the last time the node was updated |

#### Relationships
- All resources whether cluster-scoped or namespace-scoped belong to a `KubernetesCluster`.
    ```
    (:KubernetesCluster)-[:RESOURCE]->(:KubernetesNamespace,
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

### KubernetesNamespace
Representation of a [Kubernetes Namespace.](https://kubernetes.io/docs/concepts/overview/working-with-objects/namespaces/)

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


### KubernetesPod
Representation of a [Kubernetes Pod.](https://kubernetes.io/docs/concepts/workloads/pods/)

| Field | Description |
|-------|-------------|
| **id** | UID of the Kubernetes pod |
| **name** | Name of the Kubernetes pod |
| status\_phase | The phase of a Pod is a simple, high-level summary of where the Pod is in its lifecycle. |
| creation\_timestamp | Timestamp of the creation time of the Kubernetes pod |
| deletion\_timestamp | Timestamp of the deletion time of the Kubernetes pod |
| **namespace** | The Kubernetes namespace where this pod is deployed |
| labels | Labels are key-value pairs contained in the `PodSpec` and fetched from `pod.metadata.labels`. Stored as a JSON-encoded string. |
| **cluster\_name** | Name of the Kubernetes cluster where this pod is deployed |
| node | Name of the Kubernetes node where this pod is currently scheduled and running. Fetched from `pod.spec.node_name`. |
| firstseen | Timestamp of when a sync job first discovered this node |
| **lastupdated** | Timestamp of the last time the node was updated |

#### Relationships
- `KubernetesPod` has `KubernetesContainer`.
    ```
    (:KubernetesPod)-[:CONTAINS]->(:KubernetesContainer)
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
| status\_image\_id | ImageID of the container's image. |
| **status\_image\_sha** | The SHA portion of the status\_image\_id |
| status\_ready | Specifies whether the container has passed its readiness probe. |
| status\_started | Specifies whether the container has passed its startup probe. |
| **status\_state** | State of the container (running, terminated, waiting) |
| memory\_request | Minimum amount of memory guaranteed to be available to the container (e.g. "128Mi", "1Gi") |
| cpu\_request | Minimum amount of CPU guaranteed to be available to the container (e.g. "100m", "1") |
| memory\_limit | Maximum amount of memory the container is allowed to use (e.g. "256Mi", "2Gi") |
| cpu\_limit | Maximum amount of CPU the container is allowed to use (e.g. "500m", "2") |
| firstseen | Timestamp of when a sync job first discovered this node |
| **lastupdated** | Timestamp of the last time the node was updated |


#### Relationships
- `KubernetesPod` has `KubernetesContainer`.
    ```
    (:KubernetesPod)-[:CONTAINS]->(:KubernetesContainer)
    ```

- `KubernetesContainer` references container images from registries. The relationship matches containers to images by digest (`status_image_sha`).
    ```
    (:KubernetesContainer)-[:HAS_IMAGE]->(:ECRImage)
    (:KubernetesContainer)-[:HAS_IMAGE]->(:GitLabContainerImage)
    ```

### KubernetesService
Representation of a [Kubernetes Service.](https://kubernetes.io/docs/concepts/services-networking/service/)

| Field | Description |
|-------|-------------|
| **id** | UID of the kubernetes service |
| **name** | Name of the kubernetes service |
| creation\_timestamp | Timestamp of the creation time of the kubernetes service |
| deletion\_timestamp | Timestamp of the deletion time of the kubernetes service |
| **namespace** | The Kubernetes namespace where this service is deployed |
| selector | Labels used by the service to select pods. Fetched from `service.spec.selector`. Stored as a JSON-encoded string. |
| type | Type of kubernetes service e.g. `ClusterIP` |
| cluster\_ip | The internal IP address assigned to the Kubernetes service within the cluster |
| load\_balancer\_ip | IP of the load balancer when service type is `LoadBalancer` |
| load\_balancer\_ingress | The list of load balancer ingress points, typically containing the hostname and IP. Stored as a JSON-encoded string. |
| **cluster\_name** | Name of the Kubernetes cluster where this service is deployed |
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

| Field | Description |
|-------|-------------|
| **id** | Identifier for the ServiceAccount derived from cluster_name, namespace and name (e.g. `my-cluster/default/my-service-account`) |
| name | Name of the Kubernetes ServiceAccount |
| namespace | The Kubernetes namespace where this ServiceAccount is deployed |
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

- `KubernetesServiceAccount` is used as a subject in `KubernetesRoleBinding`.
    ```
    (:KubernetesRoleBinding)-[:SUBJECT]->(:KubernetesServiceAccount)
    ```

- `KubernetesServiceAccount` is used as a subject in `KubernetesClusterRoleBinding`.
    ```
    (:KubernetesClusterRoleBinding)-[:SUBJECT]->(:KubernetesServiceAccount)
    ```

### KubernetesRole
Representation of a [Kubernetes Role.](https://kubernetes.io/docs/reference/access-authn-authz/rbac/#role-and-clusterrole)

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
