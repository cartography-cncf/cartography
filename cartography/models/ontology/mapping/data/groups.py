from cartography.models.ontology.mapping.specs import OntologyFieldMapping
from cartography.models.ontology.mapping.specs import OntologyMapping
from cartography.models.ontology.mapping.specs import OntologyNodeMapping

# UserGroup fields:
# name - Display name of the group (REQUIRED)
# description - Group description
# email - Group email address

# AWS IAM
aws_mapping = OntologyMapping(
    module_name="aws",
    nodes=[
        OntologyNodeMapping(
            node_label="AWSGroup",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                # description: Not available
                # email: Not available
            ],
        ),
        OntologyNodeMapping(
            node_label="AWSSSOGroup",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="display_name", required=True
                ),
                OntologyFieldMapping(
                    ontology_field="description", node_field="description"
                ),
                # email: Not available
            ],
        ),
    ],
)

# Duo
duo_mapping = OntologyMapping(
    module_name="duo",
    nodes=[
        OntologyNodeMapping(
            node_label="DuoGroup",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                OntologyFieldMapping(ontology_field="description", node_field="desc"),
                # email: Not available
            ],
        ),
    ],
)

# Entra (formerly Azure AD)
entra_mapping = OntologyMapping(
    module_name="entra",
    nodes=[
        OntologyNodeMapping(
            node_label="EntraGroup",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="display_name", required=True
                ),
                OntologyFieldMapping(
                    ontology_field="description", node_field="description"
                ),
                OntologyFieldMapping(ontology_field="email", node_field="mail"),
            ],
        ),
    ],
)

# GitHub
github_mapping = OntologyMapping(
    module_name="github",
    nodes=[
        OntologyNodeMapping(
            node_label="GitHubTeam",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                OntologyFieldMapping(
                    ontology_field="description", node_field="description"
                ),
                # email: Not available
            ],
        ),
    ],
)

# GitLab
gitlab_mapping = OntologyMapping(
    module_name="gitlab",
    nodes=[
        OntologyNodeMapping(
            node_label="GitLabGroup",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                OntologyFieldMapping(
                    ontology_field="description", node_field="description"
                ),
                # email: Not available
            ],
        ),
    ],
)

# Google Workspace
googleworkspace_mapping = OntologyMapping(
    module_name="googleworkspace",
    nodes=[
        OntologyNodeMapping(
            node_label="GoogleWorkspaceGroup",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="display_name", required=True
                ),
                OntologyFieldMapping(
                    ontology_field="description", node_field="description"
                ),
                OntologyFieldMapping(ontology_field="email", node_field="email"),
            ],
        ),
    ],
)

# GSuite (legacy)
gsuite_mapping = OntologyMapping(
    module_name="gsuite",
    nodes=[
        OntologyNodeMapping(
            node_label="GSuiteGroup",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                OntologyFieldMapping(
                    ontology_field="description", node_field="description"
                ),
                OntologyFieldMapping(ontology_field="email", node_field="email"),
            ],
        ),
    ],
)

# Keycloak
keycloak_mapping = OntologyMapping(
    module_name="keycloak",
    nodes=[
        OntologyNodeMapping(
            node_label="KeycloakGroup",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                OntologyFieldMapping(
                    ontology_field="description", node_field="description"
                ),
                # email: Not available
            ],
        ),
    ],
)

# OCI
oci_mapping = OntologyMapping(
    module_name="oci",
    nodes=[
        OntologyNodeMapping(
            node_label="OCIGroup",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                OntologyFieldMapping(
                    ontology_field="description", node_field="description"
                ),
                # email: Not available
            ],
        ),
    ],
)

# Okta (legacy module - label and _ont_* properties set in raw Cypher)
okta_mapping = OntologyMapping(
    module_name="okta",
    nodes=[
        OntologyNodeMapping(
            node_label="OktaGroup",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                OntologyFieldMapping(
                    ontology_field="description", node_field="description"
                ),
                # email: Not available
            ],
        ),
    ],
)

# PagerDuty
pagerduty_mapping = OntologyMapping(
    module_name="pagerduty",
    nodes=[
        OntologyNodeMapping(
            node_label="PagerDutyTeam",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                OntologyFieldMapping(
                    ontology_field="description", node_field="description"
                ),
                # email: Not available
            ],
        ),
    ],
)

# Scaleway
scaleway_mapping = OntologyMapping(
    module_name="scaleway",
    nodes=[
        OntologyNodeMapping(
            node_label="ScalewayGroup",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                OntologyFieldMapping(
                    ontology_field="description", node_field="description"
                ),
                # email: Not available
            ],
        ),
    ],
)

# Slack
slack_mapping = OntologyMapping(
    module_name="slack",
    nodes=[
        OntologyNodeMapping(
            node_label="SlackGroup",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                OntologyFieldMapping(
                    ontology_field="description", node_field="description"
                ),
                # email: Not available
            ],
        ),
    ],
)

# Tailscale
tailscale_mapping = OntologyMapping(
    module_name="tailscale",
    nodes=[
        OntologyNodeMapping(
            node_label="TailscaleGroup",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                # description: Not available
                # email: Not available
            ],
        ),
    ],
)

GROUPS_ONTOLOGY_MAPPING: dict[str, OntologyMapping] = {
    "aws": aws_mapping,
    "duo": duo_mapping,
    "entra": entra_mapping,
    "github": github_mapping,
    "gitlab": gitlab_mapping,
    "googleworkspace": googleworkspace_mapping,
    "gsuite": gsuite_mapping,
    "keycloak": keycloak_mapping,
    "oci": oci_mapping,
    "okta": okta_mapping,
    "pagerduty": pagerduty_mapping,
    "scaleway": scaleway_mapping,
    "slack": slack_mapping,
    "tailscale": tailscale_mapping,
}
