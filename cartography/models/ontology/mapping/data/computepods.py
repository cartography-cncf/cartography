# Ontology mapping for the ComputePod semantic label.
#
# _ont_name - The display name of the pod / task.
# _ont_status - Pod / task runtime status, normalized to the shared canonical set:
#   running, pending, succeeded, failed, stopping, stopped, unknown.
#   The raw provider value stays on the source node's own status property.
# _ont_namespace - Namespace the pod runs in (where applicable).
# _ont_node - Node or host the pod is scheduled on (where applicable).
from cartography.models.ontology.mapping.specs import OntologyFieldMapping
from cartography.models.ontology.mapping.specs import OntologyMapping
from cartography.models.ontology.mapping.specs import OntologyNodeMapping

# AWS ECS task lastStatus
_AWS_ECS_TASK_STATUS = {
    "PROVISIONING": "pending",
    "PENDING": "pending",
    "ACTIVATING": "pending",
    "RUNNING": "running",
    "DEACTIVATING": "stopping",
    "STOPPING": "stopping",
    "DEPROVISIONING": "stopping",
    "STOPPED": "stopped",
    "DELETED": "stopped",
}

# Kubernetes PodPhase (fixtures also use lowercase "running")
_K8S_POD_STATUS = {
    "Pending": "pending",
    "Running": "running",
    "running": "running",
    "Succeeded": "succeeded",
    "Failed": "failed",
    "Unknown": "unknown",
}

aws_ecs_mapping = OntologyMapping(
    module_name="aws",
    nodes=[
        OntologyNodeMapping(
            node_label="AWSECSTask",
            fields=[
                # name: ECS tasks have no human-readable name field; the closest
                # identifier is the task ARN, already exposed as `id` / `arn`.
                OntologyFieldMapping(
                    ontology_field="status",
                    node_field="last_status",
                    special_handling="mapping",
                    extra={"map": _AWS_ECS_TASK_STATUS},
                ),
                # namespace: Not applicable for ECS (AWS does not use namespaces).
                # node: ECS surfaces a container-instance ARN rather than a node
                # name, which would not match the cross-provider semantics.
            ],
        ),
    ],
)

kubernetes_mapping = OntologyMapping(
    module_name="kubernetes",
    nodes=[
        OntologyNodeMapping(
            node_label="KubernetesPod",
            fields=[
                OntologyFieldMapping(ontology_field="name", node_field="name"),
                OntologyFieldMapping(
                    ontology_field="status",
                    node_field="status_phase",
                    special_handling="mapping",
                    extra={"map": _K8S_POD_STATUS},
                ),
                OntologyFieldMapping(
                    ontology_field="namespace", node_field="namespace"
                ),
                OntologyFieldMapping(ontology_field="node", node_field="node"),
            ],
        ),
    ],
)

azure_aci_mapping = OntologyMapping(
    module_name="azure",
    nodes=[
        OntologyNodeMapping(
            node_label="AzureGroupContainer",
            fields=[
                OntologyFieldMapping(ontology_field="name", node_field="name"),
                # status: intentionally not mapped. The group node only exposes
                # provisioning_state (an ARM deployment status: a stopped/completed
                # group is still "Succeeded"), which is not the runtime pod phase
                # this field models. Per-container runtime state lives on
                # AzureContainerInstance._ont_state instead.
                # namespace: Not applicable for Azure Container Instances.
                # node: ACI does not surface a node / host identifier.
            ],
        ),
    ],
)

COMPUTEPODS_ONTOLOGY_MAPPING: dict[str, OntologyMapping] = {
    "aws_ecs": aws_ecs_mapping,
    "kubernetes": kubernetes_mapping,
    "azure_aci": azure_aci_mapping,
}
