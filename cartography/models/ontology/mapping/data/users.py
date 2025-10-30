from cartography.models.ontology.mapping.specs import OntologyFieldMapping
from cartography.models.ontology.mapping.specs import OntologyMapping
from cartography.models.ontology.mapping.specs import OntologyNodeMapping
from cartography.models.ontology.mapping.specs import OntologyRelMapping

anthropic_mapping = OntologyMapping(
    module_name="anthropic",
    nodes=[
        OntologyNodeMapping(
            node_label="AnthropicUser",
            fields=[
                OntologyFieldMapping(
                    ontology_field="email", node_field="email", required=True
                ),
                OntologyFieldMapping(ontology_field="fullname", node_field="name"),
            ],
        ),
    ],
)

airbyte_mapping = OntologyMapping(
    module_name="airbyte",
    nodes=[
        OntologyNodeMapping(
            node_label="AirbyteUser",
            fields=[
                OntologyFieldMapping(
                    ontology_field="email", node_field="email", required=True
                ),
                OntologyFieldMapping(ontology_field="fullname", node_field="name"),
            ],
        ),
    ],
)

cloudflare_mapping = OntologyMapping(
    module_name="cloudflare",
    nodes=[
        OntologyNodeMapping(
            node_label="CloudflareMember",
            fields=[
                OntologyFieldMapping(
                    ontology_field="email", node_field="email", required=True
                ),
                OntologyFieldMapping(
                    ontology_field="firstname", node_field="firstname"
                ),
                OntologyFieldMapping(ontology_field="lastname", node_field="lastname"),
            ],
        ),
    ],
)

duo_mapping = OntologyMapping(
    module_name="duo",
    nodes=[
        OntologyNodeMapping(
            node_label="DuoUser",
            fields=[
                OntologyFieldMapping(
                    ontology_field="email", node_field="email", required=True
                ),
                OntologyFieldMapping(
                    ontology_field="firstname", node_field="firstname"
                ),
                OntologyFieldMapping(ontology_field="lastname", node_field="lastname"),
                OntologyFieldMapping(ontology_field="username", node_field="username"),
                OntologyFieldMapping(ontology_field="fullname", node_field="realname"),
            ],
        ),
    ],
)
entra_mapping = OntologyMapping(
    module_name="entra",
    nodes=[
        OntologyNodeMapping(
            node_label="EntraUser",
            fields=[
                OntologyFieldMapping(
                    ontology_field="email", node_field="email", required=True
                ),
                OntologyFieldMapping(
                    ontology_field="firstname", node_field="given_name"
                ),
                OntologyFieldMapping(ontology_field="lastname", node_field="surname"),
                OntologyFieldMapping(
                    ontology_field="fullname", node_field="display_name"
                ),
            ],
        ),
    ],
)
github_mapping = OntologyMapping(
    module_name="github",
    nodes=[
        OntologyNodeMapping(
            node_label="GitHubUser",
            fields=[
                OntologyFieldMapping(
                    ontology_field="email", node_field="email", required=True
                ),
                OntologyFieldMapping(ontology_field="username", node_field="username"),
                OntologyFieldMapping(ontology_field="fullname", node_field="fullname"),
            ],
        ),
    ],
)
gsuite_mapping = OntologyMapping(
    module_name="gsuite",
    nodes=[
        OntologyNodeMapping(
            node_label="GSuiteUser",
            fields=[
                OntologyFieldMapping(
                    ontology_field="email", node_field="email", required=True
                ),
                OntologyFieldMapping(
                    ontology_field="firstname", node_field="given_name"
                ),
                OntologyFieldMapping(
                    ontology_field="lastname", node_field="family_name"
                ),
                OntologyFieldMapping(ontology_field="fullname", node_field="name"),
            ],
        ),
    ],
)
keycloak_mapping = OntologyMapping(
    module_name="keycloak",
    nodes=[
        OntologyNodeMapping(
            node_label="KeycloakUser",
            fields=[
                OntologyFieldMapping(
                    ontology_field="email", node_field="email", required=True
                ),
                OntologyFieldMapping(ontology_field="username", node_field="username"),
                OntologyFieldMapping(
                    ontology_field="firstname", node_field="first_name"
                ),
                OntologyFieldMapping(ontology_field="lastname", node_field="last_name"),
            ],
        ),
    ],
)
lastpass_mapping = OntologyMapping(
    module_name="lastpass",
    nodes=[
        OntologyNodeMapping(
            node_label="LastpassUser",
            fields=[
                OntologyFieldMapping(
                    ontology_field="email", node_field="email", required=True
                ),
                OntologyFieldMapping(ontology_field="fullname", node_field="name"),
            ],
        ),
    ],
)
openai_mapping = OntologyMapping(
    module_name="openai",
    nodes=[
        OntologyNodeMapping(
            node_label="OpenAIUser",
            fields=[
                OntologyFieldMapping(
                    ontology_field="email", node_field="email", required=True
                ),
                OntologyFieldMapping(ontology_field="fullname", node_field="name"),
            ],
        ),
    ],
)
scaleway_mapping = OntologyMapping(
    module_name="scaleway",
    nodes=[
        OntologyNodeMapping(
            node_label="ScalewayUser",
            fields=[
                OntologyFieldMapping(
                    ontology_field="email", node_field="email", required=True
                ),
                OntologyFieldMapping(
                    ontology_field="firstname", node_field="first_name"
                ),
                OntologyFieldMapping(ontology_field="lastname", node_field="last_name"),
                OntologyFieldMapping(ontology_field="username", node_field="username"),
            ],
        ),
    ],
)
snipeit_mapping = OntologyMapping(
    module_name="snipeit",
    nodes=[
        OntologyNodeMapping(
            node_label="SnipeitUser",
            fields=[
                OntologyFieldMapping(
                    ontology_field="email", node_field="email", required=True
                ),
                OntologyFieldMapping(ontology_field="username", node_field="username"),
            ],
        ),
    ],
)
tailscale_mapping = OntologyMapping(
    module_name="tailscale",
    nodes=[
        OntologyNodeMapping(
            node_label="TailscaleUser",
            fields=[
                OntologyFieldMapping(
                    ontology_field="email", node_field="email", required=True
                ),
                OntologyFieldMapping(
                    ontology_field="fullname", node_field="display_name"
                ),
            ],
        ),
    ],
)
okta_mapping = OntologyMapping(
    module_name="okta",
    nodes=[
        OntologyNodeMapping(
            node_label="OktaUser",
            fields=[
                OntologyFieldMapping(
                    ontology_field="email", node_field="email", required=True
                ),
                OntologyFieldMapping(
                    ontology_field="firstname", node_field="first_name"
                ),
                OntologyFieldMapping(ontology_field="lastname", node_field="last_name"),
            ],
        ),
    ],
)
aws_mapping = OntologyMapping(
    module_name="aws",
    nodes=[
        OntologyNodeMapping(
            node_label="AWSUser",
            eligible_for_source=False,
            fields=[OntologyFieldMapping(ontology_field="username", node_field="name")],
        ),
        OntologyNodeMapping(
            node_label="AWSSSOUser",
            eligible_for_source=False,
            fields=[
                OntologyFieldMapping(ontology_field="username", node_field="user_name")
            ],
        ),
    ],
    rels=[
        OntologyRelMapping(
            __comment__="Link AWSSSOUser to User based on external_id mapping to arbitrary UserAccount node",
            query="MATCH (sso:AWSSSOUser) MATCH (u:User)-[:HAS_ACCOUNT]->(:UserAccount {id: sso.external_id}) MERGE (u)-[r:HAS_ACCOUNT]->(sso) ON CREATE SET r.firstseen = timestamp() SET r.lastupdated = $UPDATE_TAG",
            iterative=False,
        ),
    ],
)


USERS_ONTOLOGY_MAPPING: dict[str, OntologyMapping] = {
    "anthropic": anthropic_mapping,
    "airbyte": airbyte_mapping,
    "cloudflare": cloudflare_mapping,
    "duo": duo_mapping,
    "entra": entra_mapping,
    "github": github_mapping,
    "gsuite": gsuite_mapping,
    "keycloak": keycloak_mapping,
    "lastpass": lastpass_mapping,
    "openai": openai_mapping,
    "scaleway": scaleway_mapping,
    "snipeit": snipeit_mapping,
    "tailscale": tailscale_mapping,
    "okta": okta_mapping,
    "aws": aws_mapping,
}
