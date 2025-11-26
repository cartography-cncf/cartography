from cartography.models.ontology.mapping.specs import OntologyFieldMapping
from cartography.models.ontology.mapping.specs import OntologyMapping
from cartography.models.ontology.mapping.specs import OntologyNodeMapping

aws_ecs_container_mapping = OntologyMapping(
    module_name="aws",
    nodes=[
        OntologyNodeMapping(
            node_label="ECSContainer",
            fields=[
                OntologyFieldMapping(
                    ontology_field="id", node_field="arn", required=True
                ),
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
                OntologyFieldMapping(
                    ontology_field="id", node_field="id", required=True
                ),
                OntologyFieldMapping(ontology_field="name", node_field="name"),
                OntologyFieldMapping(ontology_field="image", node_field="image"),
                OntologyFieldMapping(
                    ontology_field="image_digest", node_field="status_image_sha"
                ),
                OntologyFieldMapping(ontology_field="state", node_field="status_state"),
                # cpu: Not exposed as a direct field in KubernetesContainer node
                # memory: Not exposed as a direct field in KubernetesContainer node
                # region: Not exposed as a direct field in KubernetesContainer node
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
                OntologyFieldMapping(
                    ontology_field="id", node_field="id", required=True
                ),
                OntologyFieldMapping(ontology_field="name", node_field="name"),
                # image: Not exposed as a direct field in AzureContainerInstance node (image info is in nested container properties)
                # image_digest: Not exposed as a direct field in AzureContainerInstance node
                OntologyFieldMapping(
                    ontology_field="state", node_field="provisioning_state"
                ),
                # cpu: Not exposed as a direct field in AzureContainerInstance node
                # memory: Not exposed as a direct field in AzureContainerInstance node
                OntologyFieldMapping(ontology_field="region", node_field="location"),
                # namespace: Not applicable for Azure Container Instances (Azure does not use namespaces in this context)
                # health_status: Not exposed as a direct field in AzureContainerInstance node
            ],
        ),
    ],
)

CONTAINER_ONTOLOGY_MAPPING: dict[str, OntologyMapping] = {
    "aws_ecs_container": aws_ecs_container_mapping,
    "kubernetes": kubernetes_mapping,
    "azure": azure_mapping,
}
