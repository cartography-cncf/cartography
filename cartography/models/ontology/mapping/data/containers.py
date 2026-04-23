from cartography.models.ontology.mapping.specs import OntologyFieldMapping
from cartography.models.ontology.mapping.specs import OntologyMapping
from cartography.models.ontology.mapping.specs import OntologyNodeMapping

aws_ecs_container_mapping = OntologyMapping(
    module_name="aws",
    nodes=[
        OntologyNodeMapping(
            node_label="ECSContainer",
            fields=[
                OntologyFieldMapping(ontology_field="name", node_field="name"),
                OntologyFieldMapping(ontology_field="image", node_field="image"),
                OntologyFieldMapping(
                    ontology_field="image_digest", node_field="image_digest"
                ),
                OntologyFieldMapping(ontology_field="state", node_field="last_status"),
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
                OntologyFieldMapping(ontology_field="state", node_field="status_state"),
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
                OntologyFieldMapping(ontology_field="state", node_field="state"),
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


CONTAINER_ONTOLOGY_MAPPING: dict[str, OntologyMapping] = {
    "aws_ecs_container": aws_ecs_container_mapping,
    "kubernetes": kubernetes_mapping,
    "azure": azure_mapping,
    "gcp": gcp_mapping,
}
