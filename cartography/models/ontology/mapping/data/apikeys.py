from cartography.models.ontology.mapping.specs import OntologyFieldMapping
from cartography.models.ontology.mapping.specs import OntologyMapping
from cartography.models.ontology.mapping.specs import OntologyNodeMapping

# APIKey fields:
# name
# created_at
# updated_at
# expires_at
# last_used_at

anthropic_mapping = OntologyMapping(
    module_name="anthropic",
    nodes=[
        OntologyNodeMapping(
            node_label="AnthropicApiKey",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                OntologyFieldMapping(
                    ontology_field="created_at", node_field="created_at"
                ),
                OntologyFieldMapping(
                    ontology_field="last_used_at", node_field="last_used_at"
                ),
            ],
        ),
    ],
)

openai_mapping = OntologyMapping(
    module_name="openai",
    nodes=[
        OntologyNodeMapping(
            node_label="OpenAIApiKey",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                OntologyFieldMapping(
                    ontology_field="created_at", node_field="created_at"
                ),
                OntologyFieldMapping(
                    ontology_field="last_used_at", node_field="last_used_at"
                ),
            ],
        ),
        OntologyNodeMapping(
            node_label="OpenAIAdminApiKey",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                OntologyFieldMapping(
                    ontology_field="created_at", node_field="created_at"
                ),
                OntologyFieldMapping(
                    ontology_field="last_used_at", node_field="last_used_at"
                ),
            ],
        ),
    ],
)

scaleway_mapping = OntologyMapping(
    module_name="scaleway",
    nodes=[
        OntologyNodeMapping(
            node_label="ScalewayApiKey",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="description", required=True
                ),
                OntologyFieldMapping(
                    ontology_field="created_at", node_field="created_at"
                ),
                OntologyFieldMapping(
                    ontology_field="updated_at", node_field="updated_at"
                ),
                OntologyFieldMapping(
                    ontology_field="expires_at", node_field="expires_at"
                ),
            ],
        ),
    ],
)

APIKEYS_ONTOLOGY_MAPPING: dict[str, OntologyMapping] = {
    "anthropic": anthropic_mapping,
    "openai": openai_mapping,
    "scaleway": scaleway_mapping,
}
