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
                # last_used_at: Not available - the Anthropic Admin API
                # (GET /v1/organizations/api_keys) does not return a
                # last_used_at field for API keys.
                # expires_at: Available upstream but not currently ingested
                # on AnthropicApiKey; add the property to the schema and map
                # it here when needed.
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

workos_apikeys_mapping = OntologyMapping(
    module_name="workos",
    nodes=[
        OntologyNodeMapping(
            node_label="WorkOSAPIKey",
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
                OntologyFieldMapping(
                    ontology_field="last_used_at", node_field="last_used_at"
                ),
            ],
        ),
    ],
)

subimage_mapping = OntologyMapping(
    module_name="subimage",
    nodes=[
        OntologyNodeMapping(
            node_label="SubImageAPIKey",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
            ],
        ),
    ],
)

aws_mapping = OntologyMapping(
    module_name="aws",
    nodes=[
        OntologyNodeMapping(
            node_label="AWSAccountAccessKey",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="accesskeyid", required=True
                ),
                OntologyFieldMapping(
                    ontology_field="created_at", node_field="createdate"
                ),
                OntologyFieldMapping(
                    ontology_field="last_used_at", node_field="lastuseddate"
                ),
            ],
        ),
    ],
)

gcp_mapping = OntologyMapping(
    module_name="gcp",
    nodes=[
        OntologyNodeMapping(
            node_label="GCPServiceAccountKey",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                OntologyFieldMapping(
                    ontology_field="created_at", node_field="valid_after_time"
                ),
                OntologyFieldMapping(
                    ontology_field="expires_at", node_field="valid_before_time"
                ),
            ],
        ),
        OntologyNodeMapping(
            node_label="GCPApiKey",
            fields=[
                # display_name is optional upstream; fall back to the resource
                # name so _ont_name is always populated.
                OntologyFieldMapping(
                    ontology_field="name",
                    node_field="display_name",
                    required=True,
                    special_handling="coalesce",
                    extra={"fields": ["name"]},
                ),
                OntologyFieldMapping(
                    ontology_field="created_at", node_field="create_time"
                ),
                OntologyFieldMapping(
                    ontology_field="updated_at", node_field="update_time"
                ),
            ],
        ),
    ],
)

github_mapping = OntologyMapping(
    module_name="github",
    nodes=[
        OntologyNodeMapping(
            node_label="GitHubPersonalAccessToken",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="token_name", required=True
                ),
                OntologyFieldMapping(ontology_field="type", node_field="token_kind"),
                OntologyFieldMapping(
                    ontology_field="created_at",
                    node_field="access_granted_at",
                    special_handling="coalesce",
                    extra={"fields": ["credential_authorized_at"]},
                ),
                OntologyFieldMapping(
                    ontology_field="expires_at", node_field="expires_at"
                ),
                OntologyFieldMapping(
                    ontology_field="last_used_at",
                    node_field="last_used_at",
                    special_handling="coalesce",
                    extra={"fields": ["credential_accessed_at"]},
                ),
            ],
        ),
    ],
)

# Railway has two token kinds: account/workspace-scoped API tokens and project tokens that
# are pinned to a single environment. Neither exposes a last-used timestamp.
railway_mapping = OntologyMapping(
    module_name="railway",
    nodes=[
        OntologyNodeMapping(
            node_label="RailwayApiToken",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                OntologyFieldMapping(
                    ontology_field="expires_at", node_field="expires_at"
                ),
                # created_at: Not available on Railway's ApiToken type.
                # last_used_at: Not available.
            ],
        ),
        OntologyNodeMapping(
            node_label="RailwayProjectToken",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                OntologyFieldMapping(
                    ontology_field="created_at", node_field="created_at"
                ),
                # expires_at: project tokens do not expire.
                # last_used_at: Not available.
            ],
        ),
    ],
)

supabase_mapping = OntologyMapping(
    module_name="supabase",
    nodes=[
        OntologyNodeMapping(
            node_label="SupabaseApiKey",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                OntologyFieldMapping(
                    ontology_field="created_at", node_field="inserted_at"
                ),
                OntologyFieldMapping(
                    ontology_field="updated_at", node_field="updated_at"
                ),
                # expires_at: Supabase project API keys do not expire.
                # last_used_at: Not exposed by the Management API.
            ],
        ),
    ],
)


APIKEYS_ONTOLOGY_MAPPING: dict[str, OntologyMapping] = {
    "anthropic": anthropic_mapping,
    "github": github_mapping,
    "openai": openai_mapping,
    "scaleway": scaleway_mapping,
    "workos": workos_apikeys_mapping,
    "subimage": subimage_mapping,
    "aws": aws_mapping,
    "gcp": gcp_mapping,
    "railway": railway_mapping,
    "supabase": supabase_mapping,
}
