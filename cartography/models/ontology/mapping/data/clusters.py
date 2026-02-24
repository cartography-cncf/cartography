from cartography.models.ontology.mapping.specs import OntologyFieldMapping
from cartography.models.ontology.mapping.specs import OntologyMapping
from cartography.models.ontology.mapping.specs import OntologyNodeMapping

aws_eks_mapping = OntologyMapping(
    module_name="aws",
    nodes=[
        OntologyNodeMapping(
            node_label="EKSCluster",
            fields=[
                OntologyFieldMapping(
                    ontology_field="id", node_field="arn", required=True,
                ),
                OntologyFieldMapping(ontology_field="name", node_field="name"),
                OntologyFieldMapping(ontology_field="region", node_field="region"),
                OntologyFieldMapping(ontology_field="version", node_field="version"),
                OntologyFieldMapping(ontology_field="endpoint", node_field="endpoint"),
                OntologyFieldMapping(ontology_field="status", node_field="status"),
            ],
        ),
    ],
)

aws_ecs_mapping = OntologyMapping(
    module_name="aws",
    nodes=[
        OntologyNodeMapping(
            node_label="ECSCluster",
            fields=[
                OntologyFieldMapping(
                    ontology_field="id", node_field="clusterArn", required=True,
                ),
                OntologyFieldMapping(
                    ontology_field="name", node_field="clusterName",
                ),
                OntologyFieldMapping(ontology_field="region", node_field="region"),
                # version: Not applicable for ECS clusters
                # endpoint: Not applicable for ECS clusters
                OntologyFieldMapping(ontology_field="status", node_field="status"),
            ],
        ),
    ],
)

aws_emr_mapping = OntologyMapping(
    module_name="aws",
    nodes=[
        OntologyNodeMapping(
            node_label="EMRCluster",
            fields=[
                OntologyFieldMapping(
                    ontology_field="id", node_field="Id", required=True,
                ),
                OntologyFieldMapping(ontology_field="name", node_field="Name"),
                OntologyFieldMapping(ontology_field="region", node_field="region"),
                OntologyFieldMapping(
                    ontology_field="version", node_field="ReleaseLabel",
                ),
                # endpoint: Not applicable for EMR clusters
                # status: Not exposed as a direct field in EMRCluster node
            ],
        ),
    ],
)

azure_aks_mapping = OntologyMapping(
    module_name="azure",
    nodes=[
        OntologyNodeMapping(
            node_label="AzureKubernetesCluster",
            fields=[
                OntologyFieldMapping(
                    ontology_field="id", node_field="id", required=True,
                ),
                OntologyFieldMapping(ontology_field="name", node_field="name"),
                OntologyFieldMapping(
                    ontology_field="region", node_field="location",
                ),
                OntologyFieldMapping(
                    ontology_field="version", node_field="kubernetes_version",
                ),
                OntologyFieldMapping(ontology_field="endpoint", node_field="fqdn"),
                OntologyFieldMapping(
                    ontology_field="status", node_field="provisioning_state",
                ),
            ],
        ),
    ],
)

gcp_gke_mapping = OntologyMapping(
    module_name="gcp",
    nodes=[
        OntologyNodeMapping(
            node_label="GKECluster",
            fields=[
                OntologyFieldMapping(
                    ontology_field="id", node_field="id", required=True,
                ),
                OntologyFieldMapping(ontology_field="name", node_field="name"),
                OntologyFieldMapping(
                    ontology_field="region", node_field="location",
                ),
                OntologyFieldMapping(
                    ontology_field="version", node_field="current_master_version",
                ),
                OntologyFieldMapping(
                    ontology_field="endpoint", node_field="endpoint",
                ),
                OntologyFieldMapping(ontology_field="status", node_field="status"),
            ],
        ),
    ],
)

kubernetes_mapping = OntologyMapping(
    module_name="kubernetes",
    nodes=[
        OntologyNodeMapping(
            node_label="KubernetesCluster",
            fields=[
                OntologyFieldMapping(
                    ontology_field="id", node_field="id", required=True,
                ),
                OntologyFieldMapping(ontology_field="name", node_field="name"),
                # region: Not available in KubernetesCluster node
                OntologyFieldMapping(
                    ontology_field="version", node_field="version",
                ),
                # endpoint: Not available in KubernetesCluster node
                # status: Not available in KubernetesCluster node
            ],
        ),
    ],
)

CLUSTERS_ONTOLOGY_MAPPING: dict[str, OntologyMapping] = {
    "aws_eks": aws_eks_mapping,
    "aws_ecs": aws_ecs_mapping,
    "aws_emr": aws_emr_mapping,
    "azure_aks": azure_aks_mapping,
    "gcp_gke": gcp_gke_mapping,
    "kubernetes": kubernetes_mapping,
}
