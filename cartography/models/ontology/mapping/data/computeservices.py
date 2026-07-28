# Ontology mapping for the ComputeService semantic label.
#
# _ont_name - The display name of the service / orchestrator.
# _ont_region - The region or location where the service is deployed.
# _ont_status - Service provisioning/operational status, normalized to the shared
#   canonical set: active, creating, updating, deleting, failed, unknown.
#   The raw provider value stays on the source node's own status property.
from cartography.models.ontology.mapping.specs import OntologyFieldMapping
from cartography.models.ontology.mapping.specs import OntologyMapping
from cartography.models.ontology.mapping.specs import OntologyNodeMapping

# AWS ECS service status
_AWS_ECS_SERVICE_STATUS = {
    "ACTIVE": "active",
    "DRAINING": "deleting",
    "INACTIVE": "deleting",
}

# Scaleway ContainerStatus
_SCALEWAY_SERVICE_STATUS = {
    "unknown": "unknown",
    "creating": "creating",
    "pending": "creating",
    "created": "creating",
    "upgrading": "updating",
    "ready": "active",
    "deleting": "deleting",
    "error": "failed",
    "locking": "failed",
    "locked": "failed",
}

aws_ecs_mapping = OntologyMapping(
    module_name="aws",
    nodes=[
        OntologyNodeMapping(
            node_label="AWSECSService",
            fields=[
                OntologyFieldMapping(ontology_field="name", node_field="name"),
                OntologyFieldMapping(ontology_field="region", node_field="region"),
                OntologyFieldMapping(
                    ontology_field="status",
                    node_field="status",
                    special_handling="mapping",
                    extra={"map": _AWS_ECS_SERVICE_STATUS},
                ),
            ],
        ),
    ],
)

gcp_cloudrun_service_mapping = OntologyMapping(
    module_name="gcp",
    nodes=[
        OntologyNodeMapping(
            node_label="GCPCloudRunService",
            fields=[
                OntologyFieldMapping(ontology_field="name", node_field="name"),
                OntologyFieldMapping(ontology_field="region", node_field="location"),
                # status: GCPCloudRunService does not surface a single provisioning
                # status field; revision-level state lives on GCPCloudRunRevision.
            ],
        ),
    ],
)

gcp_cloudrun_job_mapping = OntologyMapping(
    module_name="gcp",
    nodes=[
        OntologyNodeMapping(
            node_label="GCPCloudRunJob",
            fields=[
                OntologyFieldMapping(ontology_field="name", node_field="name"),
                OntologyFieldMapping(ontology_field="region", node_field="location"),
                # status: GCPCloudRunJob does not surface a single provisioning
                # status field; per-execution state lives on GCPCloudRunExecution.
            ],
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
                OntologyFieldMapping(ontology_field="region", node_field="region"),
                OntologyFieldMapping(
                    ontology_field="status",
                    node_field="status",
                    special_handling="mapping",
                    extra={"map": _SCALEWAY_SERVICE_STATUS},
                ),
            ],
        ),
    ],
)

# Kubernetes workload controllers are the logical-workload peer of an ECS service
# / Cloud Run service. They carry no region and no single provisioning-status
# field, so only the display name is mapped.
kubernetes_mapping = OntologyMapping(
    module_name="kubernetes",
    nodes=[
        OntologyNodeMapping(
            node_label="KubernetesDeployment",
            fields=[OntologyFieldMapping(ontology_field="name", node_field="name")],
        ),
        OntologyNodeMapping(
            node_label="KubernetesStatefulSet",
            fields=[OntologyFieldMapping(ontology_field="name", node_field="name")],
        ),
        OntologyNodeMapping(
            node_label="KubernetesDaemonSet",
            fields=[OntologyFieldMapping(ontology_field="name", node_field="name")],
        ),
        OntologyNodeMapping(
            node_label="KubernetesJob",
            fields=[OntologyFieldMapping(ontology_field="name", node_field="name")],
        ),
        OntologyNodeMapping(
            node_label="KubernetesCronJob",
            fields=[OntologyFieldMapping(ontology_field="name", node_field="name")],
        ),
    ],
)

COMPUTESERVICES_ONTOLOGY_MAPPING: dict[str, OntologyMapping] = {
    "aws_ecs": aws_ecs_mapping,
    "gcp_cloudrun_service": gcp_cloudrun_service_mapping,
    "gcp_cloudrun_job": gcp_cloudrun_job_mapping,
    "scaleway": scaleway_mapping,
    "kubernetes": kubernetes_mapping,
}
