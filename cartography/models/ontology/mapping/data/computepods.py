# Ontology mapping for the ComputePod semantic label.
#
# _ont_name - The display name of the pod / task.
# _ont_status - Current runtime status of the pod / task.
# _ont_namespace - Namespace the pod runs in (where applicable).
# _ont_node - Node or host the pod is scheduled on (where applicable).
from cartography.models.ontology.mapping.specs import OntologyFieldMapping
from cartography.models.ontology.mapping.specs import OntologyMapping
from cartography.models.ontology.mapping.specs import OntologyNodeMapping

aws_ecs_mapping = OntologyMapping(
    module_name="aws",
    nodes=[
        OntologyNodeMapping(
            node_label="ECSTask",
            fields=[
                # name: ECS tasks have no human-readable name field; the closest
                # identifier is the task ARN, already exposed as `id` / `arn`.
                OntologyFieldMapping(ontology_field="status", node_field="last_status"),
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
                    ontology_field="status", node_field="status_phase"
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
                OntologyFieldMapping(
                    ontology_field="status", node_field="provisioning_state"
                ),
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
