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
                OntologyFieldMapping(ontology_field="status", node_field="state"),
                # domain: Not available
            ],
        ),
        OntologyNodeMapping(
            node_label="AWSOrganization",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="id", required=True
                ),
                # status: Not available; feature_set is not lifecycle state.
                # domain: Not available
            ],
        ),
    ],
)

# Azure
azure_mapping = OntologyMapping(
    module_name="azure",
    nodes=[
        # AzureTenant has no mappable fields but the entry must exist so the
        # _ont_source side-effect of _build_ontology_node_properties_statement
        # fires for both AzureTenantSchema and the composite EntraTenantSchema
        # (which carries `AzureTenant` as its primary label).
        OntologyNodeMapping(node_label="AzureTenant", fields=[]),
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
    module_name="microsoft",
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

# Jamf: No field to map in JamfTenant (minimal properties)

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


# Sentry
sentry_mapping = OntologyMapping(
    module_name="sentry",
    nodes=[
        OntologyNodeMapping(
            node_label="SentryOrganization",
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

# JumpCloud
jumpcloud_mapping = OntologyMapping(
    module_name="jumpcloud",
    nodes=[
        OntologyNodeMapping(
            node_label="JumpCloudTenant",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="id", required=True
                ),
                # status: Not available
                # domain: Not available
            ],
        ),
    ],
)

# Tailscale
# TailscaleTailnet: No field to map in TailscaleTailnet (minimal properties)

# WorkOS Tenant mapping
workos_tenants_mapping = OntologyMapping(
    module_name="workos",
    nodes=[
        OntologyNodeMapping(
            node_label="WorkOSOrganization",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                # status: Not available
                # domain: Available via WorkOSOrganizationDomain relationship
            ],
        ),
    ],
)


# SubImage: SubImageTenant has no mappable Tenant fields; the entry exists
# only so _ont_source is written on the node.
subimage_mapping = OntologyMapping(
    module_name="subimage",
    nodes=[
        OntologyNodeMapping(node_label="SubImageTenant", fields=[]),
    ],
)

# Crowdstrike: CrowdstrikeTenant has no mappable Tenant fields; the entry
# exists only so _ont_source is written on the node.
crowdstrike_mapping = OntologyMapping(
    module_name="crowdstrike",
    nodes=[
        OntologyNodeMapping(node_label="CrowdstrikeTenant", fields=[]),
    ],
)

# Socket.dev
socketdev_mapping = OntologyMapping(
    module_name="socketdev",
    nodes=[
        OntologyNodeMapping(
            node_label="SocketDevOrganization",
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

# Salesforce
salesforce_mapping = OntologyMapping(
    module_name="salesforce",
    nodes=[
        OntologyNodeMapping(
            node_label="SalesforceOrganization",
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

# Vercel
vercel_mapping = OntologyMapping(
    module_name="vercel",
    nodes=[
        OntologyNodeMapping(
            node_label="VercelTeam",
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

circleci_mapping = OntologyMapping(
    module_name="circleci",
    nodes=[
        OntologyNodeMapping(
            node_label="CircleCIOrganization",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
            ],
        ),
    ],
)

TENANTS_ONTOLOGY_MAPPING: dict[str, OntologyMapping] = {
    "airbyte": airbyte_mapping,
    "aws": aws_mapping,
    "circleci": circleci_mapping,
    "azure": azure_mapping,
    "cloudflare": cloudflare_mapping,
    "crowdstrike": crowdstrike_mapping,
    "digitalocean": digitalocean_mapping,
    "microsoft": entra_mapping,
    "gcp": gcp_mapping,
    "github": github_mapping,
    "googleworkspace": googleworkspace_mapping,
    "keycloak": keycloak_mapping,
    "salesforce": salesforce_mapping,
    "okta": okta_mapping,
    "openai": openai_mapping,
    "scaleway": scaleway_mapping,
    "sentry": sentry_mapping,
    "sentinelone": sentinelone_mapping,
    "jumpcloud": jumpcloud_mapping,
    "slack": slack_mapping,
    "spacelift": spacelift_mapping,
    "subimage": subimage_mapping,
    "socketdev": socketdev_mapping,
    "workos": workos_tenants_mapping,
    "vercel": vercel_mapping,
    "databricks": OntologyMapping(
        module_name="databricks",
        nodes=[
            OntologyNodeMapping(
                node_label="DatabricksWorkspace",
                fields=[
                    OntologyFieldMapping(
                        ontology_field="name", node_field="host", required=True
                    ),
                    OntologyFieldMapping(ontology_field="domain", node_field="host"),
                ],
            ),
            OntologyNodeMapping(
                node_label="DatabricksAccount",
                fields=[
                    OntologyFieldMapping(
                        ontology_field="name", node_field="account_id", required=True
                    ),
                    OntologyFieldMapping(ontology_field="domain", node_field="host"),
                ],
            ),
        ],
    ),
}
