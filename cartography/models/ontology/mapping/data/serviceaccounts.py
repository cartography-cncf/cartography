from cartography.models.ontology.mapping.specs import OntologyFieldMapping
from cartography.models.ontology.mapping.specs import OntologyMapping
from cartography.models.ontology.mapping.specs import OntologyNodeMapping

# ServiceAccount fields:
# name - Display name of the service account (REQUIRED)
# email - Service account email address
# active - Whether the service account is active

# GCP
gcp_mapping = OntologyMapping(
    module_name="gcp",
    nodes=[
        OntologyNodeMapping(
            node_label="GCPServiceAccount",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="display_name", required=True
                ),
                OntologyFieldMapping(ontology_field="email", node_field="email"),
                OntologyFieldMapping(
                    ontology_field="active",
                    node_field="disabled",
                    special_handling="invert_boolean",
                ),
            ],
        ),
    ],
)

# Kubernetes
kubernetes_mapping = OntologyMapping(
    module_name="kubernetes",
    nodes=[
        OntologyNodeMapping(
            node_label="KubernetesServiceAccount",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                # email: Not available
                # active: Not available
            ],
        ),
    ],
)

# OpenAI
openai_mapping = OntologyMapping(
    module_name="openai",
    nodes=[
        OntologyNodeMapping(
            node_label="OpenAIServiceAccount",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                # email: Not available
                # active: Not available
            ],
        ),
    ],
)

# Scaleway
scaleway_mapping = OntologyMapping(
    module_name="scaleway",
    nodes=[
        OntologyNodeMapping(
            node_label="ScalewayApplication",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                # email: Not available
                # active: Not available
            ],
        ),
    ],
)

# AWS
aws_mapping = OntologyMapping(
    module_name="aws",
    nodes=[
        OntologyNodeMapping(
            node_label="AWSServicePrincipal",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="arn", required=True
                ),
                # email: Not available
                # active: Not available
            ],
        ),
    ],
)

# Microsoft Entra
microsoft_mapping = OntologyMapping(
    module_name="microsoft",
    nodes=[
        OntologyNodeMapping(
            node_label="EntraServicePrincipal",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="display_name", required=True
                ),
                # email: Not available
                OntologyFieldMapping(
                    ontology_field="active", node_field="account_enabled"
                ),
            ],
        ),
    ],
)

SERVICEACCOUNTS_ONTOLOGY_MAPPING: dict[str, OntologyMapping] = {
    "gcp": gcp_mapping,
    "kubernetes": kubernetes_mapping,
    "openai": openai_mapping,
    "scaleway": scaleway_mapping,
    "aws": aws_mapping,
    "microsoft": microsoft_mapping,
}
