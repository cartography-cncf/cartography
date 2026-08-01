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
            node_label="AWSSecretsManagerSecret",
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
        OntologyNodeMapping(
            node_label="AWSSSMParameter",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                OntologyFieldMapping(
                    ontology_field="updated_at", node_field="lastmodifieddate"
                ),
                # created_at: Not available on SSM Parameter
                # rotation_enabled: Not available on SSM Parameter
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

# Railway environment variables. Cartography ingests names only, never values.
railway_mapping = OntologyMapping(
    module_name="railway",
    nodes=[
        OntologyNodeMapping(
            node_label="RailwayVariable",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                OntologyFieldMapping(
                    ontology_field="created_at", node_field="created_at"
                ),
                # updated_at / rotation_enabled: Not available on Railway's Variable type.
            ],
        ),
    ],
)

supabase_mapping = OntologyMapping(
    module_name="supabase",
    nodes=[
        OntologyNodeMapping(
            node_label="SupabaseSecret",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                OntologyFieldMapping(
                    ontology_field="updated_at", node_field="updated_at"
                ),
                # created_at: Not available; the secrets endpoint returns only
                # updated_at.
                # rotation_enabled: Supabase has no managed secret rotation.
            ],
        ),
    ],
)


modal_mapping = OntologyMapping(
    module_name="modal",
    nodes=[
        OntologyNodeMapping(
            node_label="ModalSecret",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                OntologyFieldMapping(
                    ontology_field="created_at", node_field="created_at"
                ),
                # updated_at: Modal does not report when a secret was last modified.
                # rotation_enabled: Modal has no secret rotation feature.
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
    "railway": railway_mapping,
    "supabase": supabase_mapping,
    "modal": modal_mapping,
}
