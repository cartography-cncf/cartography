from cartography.models.ontology.mapping.specs import OntologyFieldMapping
from cartography.models.ontology.mapping.specs import OntologyMapping
from cartography.models.ontology.mapping.specs import OntologyNodeMapping

# Secret fields:
# name - Secret name (required)
# created_at - Creation timestamp
# updated_at - Last update timestamp
# rotation_enabled - Whether rotation is enabled

aws_mapping = OntologyMapping(
    module_name="aws",
    nodes=[
        OntologyNodeMapping(
            node_label="SecretsManagerSecret",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                OntologyFieldMapping(
                    ontology_field="created_at", node_field="created_date"
                ),
                OntologyFieldMapping(
                    ontology_field="updated_at", node_field="last_changed_date"
                ),
                OntologyFieldMapping(
                    ontology_field="rotation_enabled", node_field="rotation_enabled"
                ),
            ],
        ),
    ],
)

gcp_mapping = OntologyMapping(
    module_name="gcp",
    nodes=[
        OntologyNodeMapping(
            node_label="GCPSecretManagerSecret",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                OntologyFieldMapping(
                    ontology_field="created_at", node_field="created_date"
                ),
                OntologyFieldMapping(
                    ontology_field="rotation_enabled", node_field="rotation_enabled"
                ),
            ],
        ),
    ],
)

azure_mapping = OntologyMapping(
    module_name="azure",
    nodes=[
        OntologyNodeMapping(
            node_label="AzureKeyVaultSecret",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                OntologyFieldMapping(
                    ontology_field="created_at", node_field="created_on"
                ),
                OntologyFieldMapping(
                    ontology_field="updated_at", node_field="updated_on"
                ),
            ],
        ),
    ],
)

github_mapping = OntologyMapping(
    module_name="github",
    nodes=[
        OntologyNodeMapping(
            node_label="GitHubActionsSecret",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                OntologyFieldMapping(
                    ontology_field="created_at", node_field="created_at"
                ),
                OntologyFieldMapping(
                    ontology_field="updated_at", node_field="updated_at"
                ),
            ],
        ),
    ],
)

kubernetes_mapping = OntologyMapping(
    module_name="kubernetes",
    nodes=[
        OntologyNodeMapping(
            node_label="KubernetesSecret",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                OntologyFieldMapping(
                    ontology_field="created_at", node_field="creation_timestamp"
                ),
            ],
        ),
    ],
)

SECRETS_ONTOLOGY_MAPPING: dict[str, OntologyMapping] = {
    "aws": aws_mapping,
    "gcp": gcp_mapping,
    "azure": azure_mapping,
    "github": github_mapping,
    "kubernetes": kubernetes_mapping,
}
