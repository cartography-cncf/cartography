from cartography.models.ontology.mapping.specs import OntologyFieldMapping
from cartography.models.ontology.mapping.specs import OntologyMapping
from cartography.models.ontology.mapping.specs import OntologyNodeMapping

# Tenant fields:
# name - Display name or friendly name of the tenant/organization
# status - Current status/state of the tenant (e.g., active, suspended, archived)
# domain - Primary domain name associated with the tenant

# Airbyte
airbyte_mapping = OntologyMapping(
    module_name="airbyte",
    nodes=[
        OntologyNodeMapping(
            node_label="AirbyteOrganization",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                # status: Not available
                # domain: Not available
            ],
        ),
    ],
)

# Anthropic: No field to map in AnthropicOrganization (minimal properties)

# AWS
aws_mapping = OntologyMapping(
    module_name="aws",
    nodes=[
        OntologyNodeMapping(
            node_label="AWSAccount",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                # status: inscope/foreign fields exist but not a standard status
                # domain: Not available
            ],
        ),
    ],
)

# Azure
azure_mapping = OntologyMapping(
    module_name="azure",
    nodes=[
        # No field to map in AzureTenant (minimal properties)
        OntologyNodeMapping(
            node_label="AzureSubscription",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                OntologyFieldMapping(ontology_field="status", node_field="state"),
                # domain: Not available
            ],
        ),
    ],
)

# Cloudflare
cloudflare_mapping = OntologyMapping(
    module_name="cloudflare",
    nodes=[
        OntologyNodeMapping(
            node_label="CloudflareAccount",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                # status: Not available
                # domain: Not available (manages multiple domains)
                # enabled: Not available
            ],
        ),
    ],
)

# DigitalOcean
digitalocean_mapping = OntologyMapping(
    module_name="digitalocean",
    nodes=[
        OntologyNodeMapping(
            node_label="DOAccount",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="uuid", required=True
                ),
                OntologyFieldMapping(ontology_field="status", node_field="status"),
                # domain: Not available
            ],
        ),
        OntologyNodeMapping(
            node_label="DOProject",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                )
                # status: Not available
                # domain: Not available
            ],
        ),
    ],
)

# Entra (formerly Azure AD)
entra_mapping = OntologyMapping(
    module_name="entra",
    nodes=[
        OntologyNodeMapping(
            node_label="EntraTenant",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="display_name", required=True
                ),
                OntologyFieldMapping(ontology_field="status", node_field="state"),
                # domain: Not available (multiple domains possible)
            ],
        ),
    ],
)

# GCP
gcp_mapping = OntologyMapping(
    module_name="gcp",
    nodes=[
        OntologyNodeMapping(
            node_label="GCPOrganization",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="displayname", required=True
                ),
                OntologyFieldMapping(
                    ontology_field="status", node_field="lifecyclestate"
                ),
                # domain: Not available
            ],
        ),
        OntologyNodeMapping(
            node_label="GCPProject",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="displayname", required=True
                ),
                OntologyFieldMapping(
                    ontology_field="status", node_field="lifecyclestate"
                ),
                # domain: Not available
            ],
        ),
    ],
)

# GitHub
github_mapping = OntologyMapping(
    module_name="github",
    nodes=[
        OntologyNodeMapping(
            node_label="GitHubOrganization",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="username", required=True
                ),
                # status: Not available
                # domain: Not available
            ],
        ),
    ],
)

# Google Workspace
googleworkspace_mapping = OntologyMapping(
    module_name="googleworkspace",
    nodes=[
        OntologyNodeMapping(
            node_label="GoogleWorkspaceTenant",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                OntologyFieldMapping(ontology_field="domain", node_field="domain"),
                # status: Not available
            ],
        ),
    ],
)

# GSuite (legacy): No field to map in GSuiteTenant (minimal properties)

# Kandji: No field to map in KandjiTenant (minimal properties)


# Keycloak
keycloak_mapping = OntologyMapping(
    module_name="keycloak",
    nodes=[
        OntologyNodeMapping(
            node_label="KeycloakRealm",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                # status: Not available (but enabled is available)
                # domain: Not available (but domains tracked separately)
            ],
        ),
    ],
)

# LastPass: No field to map in LastpassTenant (minimal properties)


# Okta
okta_mapping = OntologyMapping(
    module_name="okta",
    nodes=[
        OntologyNodeMapping(
            node_label="OktaOrganization",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                # status: Not available
                # domain: Not available (part of ID)
            ],
        ),
    ],
)

# OpenAI
# OpenAIOrganization: No field to map in OpenAIOrganization (minimal properties)
openai_mapping = OntologyMapping(
    module_name="openai",
    nodes=[
        OntologyNodeMapping(
            node_label="OpenAIProject",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                OntologyFieldMapping(ontology_field="status", node_field="status"),
                # domain: Not available
            ],
        ),
    ],
)

# Scaleway
# ScalewayOrganization: No field to map in ScalewayOrganization (minimal properties)
scaleway_mapping = OntologyMapping(
    module_name="scaleway",
    nodes=[
        OntologyNodeMapping(
            node_label="ScalewayProject",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                # status: Not available
                # domain: Not available
            ],
        ),
    ],
)


# SentinelOne
sentinelone_mapping = OntologyMapping(
    module_name="sentinelone",
    nodes=[
        OntologyNodeMapping(
            node_label="S1Account",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                OntologyFieldMapping(ontology_field="status", node_field="state"),
                # domain: Not available
            ],
        ),
    ],
)

# SnipeIT: No field to map in SnipeITTenant (minimal properties)


# Spacelift
spacelift_mapping = OntologyMapping(
    module_name="spacelift",
    nodes=[
        OntologyNodeMapping(
            node_label="SpaceliftAccount",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                # status: Not available
                # domain: Not available
            ],
        ),
    ],
)

# Slack
slack_mapping = OntologyMapping(
    module_name="slack",
    nodes=[
        OntologyNodeMapping(
            node_label="SlackTeam",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                OntologyFieldMapping(ontology_field="domain", node_field="domain"),
                # status: Not available
            ],
        ),
    ],
)

# Duo
# DuoApiHost: No field to map in DuoApiHost (minimal properties)

# Tailscale
# TailscaleTailnet: No field to map in TailscaleTailnet (minimal properties)


TENANTS_ONTOLOGY_MAPPING: dict[str, OntologyMapping] = {
    "airbyte": airbyte_mapping,
    "aws": aws_mapping,
    "azure": azure_mapping,
    "cloudflare": cloudflare_mapping,
    "digitalocean": digitalocean_mapping,
    "entra": entra_mapping,
    "gcp": gcp_mapping,
    "github": github_mapping,
    "googleworkspace": googleworkspace_mapping,
    "keycloak": keycloak_mapping,
    "okta": okta_mapping,
    "openai": openai_mapping,
    "scaleway": scaleway_mapping,
    "sentinelone": sentinelone_mapping,
    "slack": slack_mapping,
    "spacelift": spacelift_mapping,
}
