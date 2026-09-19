# Cloud Run

Google Cloud Run is a serverless compute platform for running containers.
Cartography models services, revisions, jobs, executions, and the container
specifications used by services and jobs. Service and job containers carry the
cross-provider `Container` label and link to resolved images.

```mermaid
graph LR
    Project[GCPProject] -->|RESOURCE| Service[GCPCloudRunService]
    Project -->|RESOURCE| Revision[GCPCloudRunRevision]
    Project -->|RESOURCE| Job[GCPCloudRunJob]
    Project -->|RESOURCE| Execution[GCPCloudRunExecution]
    Service -->|HAS_REVISION| Revision
    Service -->|CONTAINS| ServiceContainer[GCPCloudRunServiceContainer]
    Service -->|WORKLOAD_PARENT| ServiceContainer
    Job -->|HAS_EXECUTION| Execution
    Job -->|CONTAINS| JobContainer[GCPCloudRunJobContainer]
    Job -->|WORKLOAD_PARENT| JobContainer
    Service -->|RUNS_AS| ServiceAccount[GCPServiceAccount]
    Job -->|RUNS_AS| ServiceAccount
    ServiceContainer -->|HAS_IMAGE| Image[Image]
    JobContainer -->|HAS_IMAGE| Image
```

Cloud Run services are modeled as compute services. Container specifications
from each service's latest ready revision are materialized as child service
container nodes. Older revisions remain version metadata and do not duplicate
container image data.

Cloud Run jobs are grouping nodes. Their image reference, digest, architecture,
and container ontology data live on child job container nodes.

`WORKLOAD_PARENT` is the canonical parent edge for both container types.
`CONTAINS` is retained as a deprecated compatibility edge until v1.0.0.
`HAS_IMAGE` links containers to the concrete registry image type resolved from
their image reference, including Artifact Registry, ECR, GitHub Container
Registry, and GitLab Container Registry images.
