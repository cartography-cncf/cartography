## Kubernetes Schema

### KubernetesCluster
Representation of a [Kubernetes Cluster.](https://kubernetes.io/docs/concepts/overview/what-is-kubernetes/)

| Field | Description |
|-------|-------------|
| id | Identifier for the cluster i.e. UID of `kube-system` namespace |
| name | Name assigned to the cluster which is derived from kubeconfig context |
| creation\_timestamp | Timestamp of when the cluster was created i.e. creation of `kube-system` namespace |
| external\_id | Identifier for the cluster fetched from the kubeconfig context. For EKS clusters this should be the `arn`.|
| version | Git version of the Kubernetes cluster (e.g. v1.27.3) |
| version\_major | Major version number of the Kubernetes cluster (e.g. 1) |
| version\_minor | Minor version number of the Kubernetes cluster (e.g. 27) |
| go_version | Version of Go used to compile Kubernetes (e.g. go1.20.5) |
| compiler | Compiler used to build Kubernetes (e.g. gc) |
| platform | Operating system and architecture the cluster is running on (e.g. linux/amd64) |
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |

#### Relationships
- All resources whether cluster-scoped or namespace-scoped belong to a `KubernetesCluster`.
    ```
    (:KubernetesCluster)-[:RESOURCE]->(:KubernetesNamespace,
                                       :KubernetesPod,
                                       :KubernetesContainer,
                                       :KubernetesService,
                                       :KubernetesSecret,
                                       ...)
    ```

- A `KubernetesPod` belongs to a `KubernetesCluster`
    ```
    (:KubernetesCluster)-[:RESOURCE]->(:KubernetesPod)
    ```

### KubernetesNamespace
Representation of a [Kubernetes Namespace.](https://kubernetes.io/docs/concepts/overview/working-with-objects/namespaces/)

| Field | Description |
|-------|-------------|
| id | UID of the Kubernetes namespace |
| name | Name of the Kubernetes namespace |
| creation\_timestamp | Timestamp of the creation time of the Kubernetes namespace |
| deletion\_timestamp | Timestamp of the deletion time of the Kubernetes namespace |
| status\_phase | The phase of a Kubernetes namespace indicates whether it is active, terminating, or terminated |
| cluster\_name | The name of the Kubernetes cluster this namespace belongs to |
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |

#### Relationships
- All namespace-scoped resources belong to a `KubernetesNamespace`.
    ```
    (:KubernetesNamespace)-[:CONTAINS]->(:KubernetesPod,
                                         :KubernetesContainer,
                                         :KubernetesService,
                                         :KubernetesSecret,
                                         ...)
    ```


### KubernetesPod
Representation of a [Kubernetes Pod.](https://kubernetes.io/docs/concepts/workloads/pods/)

| Field | Description |
|-------|-------------|
| id | UID of the Kubernetes pod |
| name | Name of the Kubernetes pod |
| status\_phase | The phase of a Pod is a simple, high-level summary of where the Pod is in its lifecycle. |
| creation\_timestamp | Timestamp of the creation time of the Kubernetes pod |
| deletion\_timestamp | Timestamp of the deletion time of the Kubernetes pod |
| namespace | The Kubernetes namespace where this pod is deployed |
| labels | Labels are key-value pairs contained in the `PodSpec` and fetched from `pod.metadata.labels`. Stored as a JSON-encoded string. |
| cluster\_name | Name of the Kubernetes cluster where this pod is deployed |
| node | Name of the Kubernetes node where this pod is currently scheduled and running. Fetched from `pod.spec.node_name`. |
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |

#### Relationships
- `KubernetesPod` has `KubernetesContainer`.
    ```
    (:KubernetesPod)-[:CONTAINS]->(:KubernetesContainer)
    ```

### KubernetesContainer
Representation of a [Kubernetes Container.](https://kubernetes.io/docs/concepts/workloads/pods/#how-pods-manage-multiple-containers)

| Field | Description |
|-------|-------------|
| id | Identifier for the container which is derived from the UID of pod and the name of container |
| name | Name of the container in kubernetes pod |
| image | Docker image used in the container |
| namespace | The Kubernetes namespace where this container is deployed |
| cluster\_name | Name of the Kubernetes cluster where this container is deployed |
| image\_pull_policy | The policy that determines when the kubelet attempts to pull the specified image (Always, Never, IfNotPresent) |
| status\_image\_id | ImageID of the container's image. |
| status\_image\_sha | The SHA portion of the status\_image\_id |
| status\_ready | Specifies whether the container has passed its readiness probe. |
| status\_started | Specifies whether the container has passed its startup probe. |
| status\_state | State of the container (running, terminated, waiting) |
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |


#### Relationships
- `KubernetesPod` has `KubernetesContainer`.
    ```
    (:KubernetesPod)-[:CONTAINS]->(:KubernetesContainer)
    ```

### KubernetesService
Representation of a [Kubernetes Service.](https://kubernetes.io/docs/concepts/services-networking/service/)

| Field | Description |
|-------|-------------|
| id | UID of the kubernetes service |
| name | Name of the kubernetes service |
| creation\_timestamp | Timestamp of the creation time of the kubernetes service |
| deletion\_timestamp | Timestamp of the deletion time of the kubernetes service |
| namespace | The Kubernetes namespace where this service is deployed |
| selector | Labels used by the service to select pods. Fetched from `service.spec.selector`. Stored as a JSON-encoded string. |
| type | Type of kubernetes service e.g. `ClusterIP` |
| cluster\_ip | The internal IP address assigned to the Kubernetes service within the cluster |
| load\_balancer\_ip | IP of the load balancer when service type is `LoadBalancer` |
| load\_balancer\_ingress | The list of load balancer ingress points, typically containing the hostname and IP. Stored as a JSON-encoded string. |
| cluster\_name | Name of the Kubernetes cluster where this service is deployed |
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |

#### Relationships
- `KubernetesService` targets `KubernetesPod`.
    ```
    (:KubernetesService)-[:TARGETS]->(:KubernetesPod)
    ```

### KubernetesSecret
Representation of a [Kubernetes Secret.](https://kubernetes.io/docs/concepts/configuration/secret/)

| Field | Description |
|-------|-------------|
| id | UID of the kubernetes secret |
| name | Name of the kubernetes secret |
| creation\_timestamp | Timestamp of the creation time of the kubernetes secret |
| deletion\_timestamp | Timestamp of the deletion time of the kubernetes secret |
| namespace | The Kubernetes namespace where this secret is deployed |
| owner\_references | References to objects that own this secret. Useful if a secret is an `ExternalSecret`. Fetched from `secret.metadata.owner_references`. Stored as a JSON-encoded string |
| type | Type of kubernetes secret (e.g. `Opaque`) |
| cluster\_name | Name of the Kubernetes cluster where this secret is deployed |
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |

#### Relationships
- `KubernetesNamespace` has `KubernetesSecret`.
    ```
    (:KubernetesNamespace)-[:CONTAINS]->(:KubernetesSecret)
    ```
