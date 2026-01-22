from cartography.models.ontology.mapping.specs import OntologyFieldMapping
from cartography.models.ontology.mapping.specs import OntologyMapping
from cartography.models.ontology.mapping.specs import OntologyNodeMapping

entra_mapping = OntologyMapping(
    module_name="entra",
    nodes=[
        OntologyNodeMapping(
            node_label="EntraUser",
            fields=[
                OntologyFieldMapping(
                    ontology_field="email",
                    node_field="email",
                    required=True,
                ),
                OntologyFieldMapping(
                    ontology_field="firstname", node_field="given_name"
                ),
                OntologyFieldMapping(ontology_field="lastname", node_field="surname"),
                OntologyFieldMapping(
                    ontology_field="fullname", node_field="display_name"
                ),
                OntologyFieldMapping(
                    ontology_field="active", node_field="account_enabled"
                ),
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
                OntologyFieldMapping(
                    ontology_field="has_mfa",
                    node_field="multifactor",
                    special_handling="to_boolean",
                ),
                OntologyFieldMapping(
                    ontology_field="active",
                    node_field="disabled",
                    special_handling="invert_boolean",
                ),
                OntologyFieldMapping(
                    ontology_field="lastactivity", node_field="last_login"
                ),
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
                OntologyFieldMapping(
                    ontology_field="has_mfa", node_field="is_enrolled_in_2_sv"
                ),
                OntologyFieldMapping(
                    ontology_field="active",
                    node_field="suspended",
                    extra={"fields": ["archived"]},
                    special_handling="nor_boolean",
                ),
                OntologyFieldMapping(
                    ontology_field="lastactivity", node_field="last_login_time"
                ),
            ],
        ),
    ],
)
googleworkspace_mapping = OntologyMapping(
    module_name="googleworkspace",
    nodes=[
        OntologyNodeMapping(
            node_label="GoogleWorkspaceUser",
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
                OntologyFieldMapping(
                    ontology_field="has_mfa", node_field="is_enrolled_in_2_sv"
                ),
                OntologyFieldMapping(
                    ontology_field="active",
                    node_field="suspended",
                    extra={"fields": ["archived"]},
                    special_handling="nor_boolean",
                ),
                OntologyFieldMapping(
                    ontology_field="lastactivity", node_field="last_login_time"
                ),
            ],
        ),
    ],
)
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
                OntologyFieldMapping(
                    ontology_field="active",
                    node_field="status",
                    extra={"values": ["accepted"]},
                    special_handling="equal_boolean",
                ),
                OntologyFieldMapping(
                    ontology_field="has_mfa",
                    node_field="two_factor_authentication_enabled",
                ),
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
                OntologyFieldMapping(
                    ontology_field="lastactivity", node_field="last_login"
                ),
                OntologyFieldMapping(
                    ontology_field="active",
                    node_field="status",
                    extra={"values": ["active", "bypass"]},
                    special_handling="equal_boolean",
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
                OntologyFieldMapping(
                    ontology_field="has_mfa", node_field="has_2fa_enabled"
                ),
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
                OntologyFieldMapping(
                    ontology_field="active",
                    node_field="enabled",
                ),
                OntologyFieldMapping(ontology_field="has_mfa", node_field="totp"),
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
                OntologyFieldMapping(
                    ontology_field="active",
                    node_field="locked",
                    special_handling="invert_boolean",
                ),
                OntologyFieldMapping(
                    ontology_field="lastactivity", node_field="last_login_at"
                ),
                OntologyFieldMapping(ontology_field="has_mfa", node_field="mfa"),
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
                OntologyFieldMapping(
                    ontology_field="username", node_field="login_name"
                ),
                OntologyFieldMapping(
                    ontology_field="active",
                    node_field="status",
                    extra={"values": ["active", "idle"]},
                    special_handling="equal_boolean",
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
                OntologyFieldMapping(
                    ontology_field="lastactivity", node_field="last_login"
                ),
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
            fields=[
                OntologyFieldMapping(ontology_field="username", node_field="name"),
                OntologyFieldMapping(
                    ontology_field="lastactivity", node_field="passwordlastused"
                ),
            ],
        ),
        OntologyNodeMapping(
            node_label="AWSSSOUser",
            eligible_for_source=False,
            fields=[
                OntologyFieldMapping(ontology_field="username", node_field="user_name")
            ],
        ),
    ],
)
slack_mapping = OntologyMapping(
    module_name="slack",
    nodes=[
        OntologyNodeMapping(
            node_label="SlackUser",
            fields=[
                OntologyFieldMapping(ontology_field="email", node_field="email"),
                OntologyFieldMapping(ontology_field="username", node_field="name"),
                OntologyFieldMapping(
                    ontology_field="firstname", node_field="first_name"
                ),
                OntologyFieldMapping(ontology_field="lastname", node_field="last_name"),
                OntologyFieldMapping(ontology_field="fullname", node_field="real_name"),
                OntologyFieldMapping(ontology_field="has_mfa", node_field="has_mfa"),
                OntologyFieldMapping(ontology_field="inactive", node_field="deleted"),
                OntologyFieldMapping(
                    ontology_field="system_account",
                    node_field="is_bot",
                    extra={"fields": ["is_app_user"]},
                    special_handling="or_boolean",
                ),
            ],
        ),
    ],
)

# UserAccount fields:
# has_mfa
# inactive
# lastactivity

USERACCOUNTS_ONTOLOGY_MAPPING: dict[str, OntologyMapping] = {
    "entra": entra_mapping,
    "lastpass": lastpass_mapping,
    "gsuite": gsuite_mapping,
    "anthropic": anthropic_mapping,
    "airbyte": airbyte_mapping,
    "cloudflare": cloudflare_mapping,
    "duo": duo_mapping,
    "github": github_mapping,
    "keycloak": keycloak_mapping,
    "openai": openai_mapping,
    "scaleway": scaleway_mapping,
    "snipeit": snipeit_mapping,
    "tailscale": tailscale_mapping,
    "okta": okta_mapping,
    "aws": aws_mapping,
    "googleworkspace": googleworkspace_mapping,
    "slack": slack_mapping,
}
