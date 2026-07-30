from cartography.models.ontology.mapping.specs import OntologyFieldMapping
from cartography.models.ontology.mapping.specs import OntologyMapping
from cartography.models.ontology.mapping.specs import OntologyNodeMapping

# Container fields:
# _ont_state - Normalized runtime state of the container, mapped from each provider's
#   vocabulary to the shared canonical set: running, pending, stopping, stopped,
#   terminated, suspended, error, unknown. The raw value stays on the source node.

# AWS ECS container lastStatus
_AWS_ECS_CONTAINER_STATE = {
    "PROVISIONING": "pending",
    "PENDING": "pending",
    "RUNNING": "running",
    "DEPROVISIONING": "stopping",
    "STOPPED": "stopped",
}

# Kubernetes ContainerState
_K8S_CONTAINER_STATE = {
    "running": "running",
    "waiting": "pending",
    "terminated": "terminated",
}

# Azure Container Instance currentState.state
_AZURE_ACI_CONTAINER_STATE = {
    "Waiting": "pending",
    "Running": "running",
    "Terminated": "terminated",
}

# Scaleway ContainerStatus
_SCALEWAY_CONTAINER_STATE = {
    "unknown": "unknown",
    "creating": "pending",
    "created": "pending",
    "pending": "pending",
    "upgrading": "pending",
    "ready": "running",
    "deleting": "terminated",
    "error": "error",
    "locking": "suspended",
    "locked": "suspended",
}

aws_ecs_container_mapping = OntologyMapping(
    module_name="aws",
    nodes=[
        OntologyNodeMapping(
            node_label="AWSECSContainer",
            fields=[
                OntologyFieldMapping(ontology_field="name", node_field="name"),
                OntologyFieldMapping(ontology_field="image", node_field="image"),
                OntologyFieldMapping(
                    ontology_field="image_digest", node_field="image_digest"
                ),
                OntologyFieldMapping(
                    ontology_field="state",
                    node_field="last_status",
                    special_handling="mapping",
                    extra={"map": _AWS_ECS_CONTAINER_STATE},
                ),
                OntologyFieldMapping(ontology_field="cpu", node_field="cpu"),
                OntologyFieldMapping(ontology_field="memory", node_field="memory"),
                OntologyFieldMapping(ontology_field="region", node_field="region"),
                # namespace: Not applicable for ECS containers (AWS does not use namespaces)
                OntologyFieldMapping(
                    ontology_field="health_status", node_field="health_status"
                ),
            ],
        ),
    ],
)

kubernetes_mapping = OntologyMapping(
    module_name="kubernetes",
    nodes=[
        OntologyNodeMapping(
            node_label="KubernetesContainer",
            fields=[
                OntologyFieldMapping(ontology_field="name", node_field="name"),
                OntologyFieldMapping(ontology_field="image", node_field="image"),
                OntologyFieldMapping(
                    ontology_field="image_digest", node_field="status_image_sha"
                ),
                OntologyFieldMapping(
                    ontology_field="state",
                    node_field="status_state",
                    special_handling="mapping",
                    extra={"map": _K8S_CONTAINER_STATE},
                ),
                # cpu: Not exposed as a direct field in KubernetesContainer node
                # memory: Not exposed as a direct field in KubernetesContainer node
                OntologyFieldMapping(ontology_field="region", node_field="region"),
                OntologyFieldMapping(
                    ontology_field="namespace", node_field="namespace"
                ),
                # health_status: Kubernetes uses status_ready and status_started separately, not a unified health_status field
            ],
        ),
    ],
)

azure_mapping = OntologyMapping(
    module_name="azure",
    nodes=[
        OntologyNodeMapping(
            node_label="AzureContainerInstance",
            fields=[
                OntologyFieldMapping(ontology_field="name", node_field="name"),
                OntologyFieldMapping(ontology_field="image", node_field="image"),
                OntologyFieldMapping(
                    ontology_field="image_digest", node_field="image_digest"
                ),
                # ACI exposes per-container runtime state via instanceView.currentState.state,
                # distinct from the group's provisioning_state.
                OntologyFieldMapping(
                    ontology_field="state",
                    node_field="state",
                    special_handling="mapping",
                    extra={"map": _AZURE_ACI_CONTAINER_STATE},
                ),
                # cpu: Node exposes cpu_request/cpu_limit rather than a single cpu value; skip to avoid ambiguity
                # memory: Node exposes memory_request_gb/memory_limit_gb (GB) which does not match the ontology MB unit
                # region: Not per-container on Azure; location lives on the parent AzureGroupContainer
                # namespace: Not applicable for Azure Container Instances (Azure does not use namespaces in this context)
                # health_status: Not exposed as a direct field in AzureContainerInstance node
            ],
        ),
    ],
)

# Cloud Run Service/Job container nodes are declarative spec entries, not runtime instances:
# per-invocation runtime state lives on GCPCloudRunExecution (Jobs) or on serving revisions (Services).
# We encode "running" statically so :Container consumers can query "containers that are running or
# can be launched" uniformly across providers — once a Service/Job exists, its container spec is by
# construction ready to run on the next request/execution.
_GCP_CLOUDRUN_CONTAINER_FIELDS = [
    OntologyFieldMapping(ontology_field="name", node_field="name"),
    OntologyFieldMapping(ontology_field="image", node_field="image"),
    OntologyFieldMapping(ontology_field="image_digest", node_field="image_digest"),
    OntologyFieldMapping(
        ontology_field="state",
        node_field="",
        special_handling="static_value",
        extra={"value": "running"},
    ),
    # cpu: Not exposed as a direct field on the container node
    # memory: Not exposed as a direct field on the container node
    # region: Not per-container; location lives on the parent Job/Service
    # namespace: Not applicable for Cloud Run
    # health_status: Not exposed as a direct field on the container node
]


gcp_mapping = OntologyMapping(
    module_name="gcp",
    nodes=[
        OntologyNodeMapping(
            node_label="GCPCloudRunJobContainer",
            fields=_GCP_CLOUDRUN_CONTAINER_FIELDS,
        ),
        OntologyNodeMapping(
            node_label="GCPCloudRunServiceContainer",
            fields=_GCP_CLOUDRUN_CONTAINER_FIELDS,
        ),
    ],
)


scaleway_mapping = OntologyMapping(
    module_name="scaleway",
    nodes=[
        OntologyNodeMapping(
            node_label="ScalewayServerlessContainer",
            fields=[
                OntologyFieldMapping(ontology_field="name", node_field="name"),
                OntologyFieldMapping(
                    ontology_field="image", node_field="registry_image"
                ),
                OntologyFieldMapping(
                    ontology_field="state",
                    node_field="status",
                    special_handling="mapping",
                    extra={"map": _SCALEWAY_CONTAINER_STATE},
                ),
                OntologyFieldMapping(ontology_field="region", node_field="region"),
            ],
        ),
    ],
)

# Railway deployment status; see also _RAILWAY_SERVICE_STATUS in computeservices.py.
_RAILWAY_DEPLOYMENT_STATE = {
    "QUEUED": "pending",
    "INITIALIZING": "pending",
    "BUILDING": "pending",
    "DEPLOYING": "pending",
    "WAITING": "pending",
    "NEEDS_APPROVAL": "pending",
    "SUCCESS": "running",
    # A sleeping deployment is scaled to zero but still configured, which is the same
    # distinction Scaleway draws with "locked" -> suspended.
    "SLEEPING": "suspended",
    "REMOVING": "stopping",
    "REMOVED": "terminated",
    "FAILED": "error",
    "CRASHED": "error",
    "SKIPPED": "unknown",
}

# A Railway deployment is one concrete running revision of a service instance, the same
# role GCPCloudRunServiceContainer plays for a Cloud Run service. Railway exposes no name,
# image reference, resource limits or health probe on the deployment itself - the image
# lives on the parent RailwayServiceInstance - so only the lifecycle state is mapped.
railway_mapping = OntologyMapping(
    module_name="railway",
    nodes=[
        OntologyNodeMapping(
            node_label="RailwayDeployment",
            fields=[
                OntologyFieldMapping(
                    ontology_field="state",
                    node_field="status",
                    special_handling="mapping",
                    extra={"map": _RAILWAY_DEPLOYMENT_STATE},
                ),
                # name / image / image_digest / cpu / memory / region / health_status:
                # Not available on Railway's Deployment type.
            ],
        ),
    ],
)

# Modal sandbox state. SandboxInfo has no state field, so cartography derives one from the
# task result plus readiness: PENDING and RUNNING are synthetic, the rest are raw
# GENERIC_STATUS_* values. A sandbox that ran to completion is "terminated" rather than
# "stopped", since Modal sandboxes are not restartable.
_MODAL_SANDBOX_STATE = {
    "PENDING": "pending",
    "RUNNING": "running",
    "GENERIC_STATUS_UNSPECIFIED": "unknown",
    "GENERIC_STATUS_SUCCESS": "terminated",
    "GENERIC_STATUS_TERMINATED": "terminated",
    "GENERIC_STATUS_IDLE_TIMEOUT": "terminated",
    "GENERIC_STATUS_FAILURE": "error",
    "GENERIC_STATUS_TIMEOUT": "error",
    "GENERIC_STATUS_INIT_FAILURE": "error",
    "GENERIC_STATUS_INTERNAL_FAILURE": "error",
}

modal_mapping = OntologyMapping(
    module_name="modal",
    nodes=[
        OntologyNodeMapping(
            node_label="ModalSandbox",
            fields=[
                OntologyFieldMapping(ontology_field="name", node_field="name"),
                OntologyFieldMapping(
                    ontology_field="state",
                    node_field="state",
                    special_handling="mapping",
                    extra={"map": _MODAL_SANDBOX_STATE},
                ),
                OntologyFieldMapping(ontology_field="memory", node_field="memory_mb"),
                # Set only for a single-region sandbox; null when several are allowed.
                OntologyFieldMapping(ontology_field="region", node_field="region"),
                OntologyFieldMapping(
                    ontology_field="namespace", node_field="environment_name"
                ),
                # cpu: milli_cpu is millicores, which is not the ontology's vCPU unit.
                # image / image_digest: Modal image ids are neither digests nor pull URIs.
                # health_status: readiness_probe is a probe spec, not an observed result.
            ],
        ),
    ],
)

CONTAINER_ONTOLOGY_MAPPING: dict[str, OntologyMapping] = {
    "aws_ecs_container": aws_ecs_container_mapping,
    "kubernetes": kubernetes_mapping,
    "azure": azure_mapping,
    "gcp": gcp_mapping,
    "scaleway": scaleway_mapping,
    "railway": railway_mapping,
    "modal": modal_mapping,
}
