from cartography.models.ontology.mapping.specs import OntologyFieldMapping
from cartography.models.ontology.mapping.specs import OntologyMapping
from cartography.models.ontology.mapping.specs import OntologyNodeMapping

# PermissionRole fields:
# name - Display name of the role (REQUIRED)
# type - Whether the role is builtin or custom
# scope - The scope level (org/project/namespace/account/cluster/compartment)

# AWS IAM
aws_mapping = OntologyMapping(
    module_name="aws",
    nodes=[
        OntologyNodeMapping(
            node_label="AWSRole",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                OntologyFieldMapping(
                    ontology_field="type",
                    node_field="",
                    special_handling="static_value",
                    extra={"value": "custom"},
                ),
                OntologyFieldMapping(
                    ontology_field="scope",
                    node_field="",
                    special_handling="static_value",
                    extra={"value": "account"},
                ),
            ],
        ),
        OntologyNodeMapping(
            node_label="AWSPermissionSet",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                OntologyFieldMapping(
                    ontology_field="type",
                    node_field="",
                    special_handling="static_value",
                    extra={"value": "custom"},
                ),
                OntologyFieldMapping(
                    ontology_field="scope",
                    node_field="",
                    special_handling="static_value",
                    extra={"value": "org"},
                ),
            ],
        ),
    ],
)

# Azure
azure_mapping = OntologyMapping(
    module_name="azure",
    nodes=[
        OntologyNodeMapping(
            node_label="AzureRoleDefinition",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="role_name", required=True
                ),
                # _ont_type: Not reliably available (no roleType field in current model)
                # _ont_scope: assignable_scopes is a list, not a simple scope level
            ],
        ),
    ],
)

# GCP
gcp_mapping = OntologyMapping(
    module_name="gcp",
    nodes=[
        OntologyNodeMapping(
            node_label="GCPRole",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name",
                    node_field="title",
                    required=True,
                ),
                OntologyFieldMapping(
                    ontology_field="type",
                    node_field="role_type",
                    special_handling="mapping",
                    extra={
                        "map": {
                            "BASIC": "builtin",
                            "PREDEFINED": "builtin",
                            "CUSTOM": "custom",
                        }
                    },
                ),
                OntologyFieldMapping(
                    ontology_field="scope",
                    node_field="scope",
                    special_handling="mapping",
                    extra={
                        "map": {
                            "GLOBAL": "global",
                            "ORGANIZATION": "org",
                            "PROJECT": "project",
                        }
                    },
                ),
            ],
        ),
    ],
)

# Keycloak
keycloak_mapping = OntologyMapping(
    module_name="keycloak",
    nodes=[
        OntologyNodeMapping(
            node_label="KeycloakRole",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                # _ont_type: Not available
                # _ont_scope: client_role boolean indicates client vs realm scope
            ],
        ),
    ],
)

# Kubernetes
kubernetes_mapping = OntologyMapping(
    module_name="kubernetes",
    nodes=[
        OntologyNodeMapping(
            node_label="KubernetesRole",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                OntologyFieldMapping(
                    ontology_field="scope",
                    node_field="",
                    special_handling="static_value",
                    extra={"value": "namespace"},
                ),
            ],
        ),
        OntologyNodeMapping(
            node_label="KubernetesClusterRole",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                OntologyFieldMapping(
                    ontology_field="scope",
                    node_field="",
                    special_handling="static_value",
                    extra={"value": "cluster"},
                ),
            ],
        ),
    ],
)

# Cloudflare
cloudflare_mapping = OntologyMapping(
    module_name="cloudflare",
    nodes=[
        OntologyNodeMapping(
            node_label="CloudflareRole",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                OntologyFieldMapping(
                    ontology_field="type",
                    node_field="",
                    special_handling="static_value",
                    extra={"value": "builtin"},
                ),
                OntologyFieldMapping(
                    ontology_field="scope",
                    node_field="",
                    special_handling="static_value",
                    extra={"value": "account"},
                ),
            ],
        ),
    ],
)

# OCI
oci_mapping = OntologyMapping(
    module_name="oci",
    nodes=[
        OntologyNodeMapping(
            node_label="OCIPolicy",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                OntologyFieldMapping(
                    ontology_field="type",
                    node_field="",
                    special_handling="static_value",
                    extra={"value": "custom"},
                ),
                # _ont_scope: OCI policies can be tenancy-level or compartment-level;
                # deriving scope from parent relationship is needed for accuracy
            ],
        ),
    ],
)

# Okta
okta_mapping = OntologyMapping(
    module_name="okta",
    nodes=[
        OntologyNodeMapping(
            node_label="OktaAdministrationRole",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="label", required=True
                ),
                OntologyFieldMapping(
                    ontology_field="type",
                    node_field="",
                    special_handling="static_value",
                    extra={"value": "builtin"},
                ),
                OntologyFieldMapping(
                    ontology_field="scope",
                    node_field="",
                    special_handling="static_value",
                    extra={"value": "org"},
                ),
            ],
        ),
    ],
)


# Scaleway
scaleway_mapping = OntologyMapping(
    module_name="scaleway",
    nodes=[
        OntologyNodeMapping(
            node_label="ScalewayPermissionSet",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                OntologyFieldMapping(
                    ontology_field="type",
                    node_field="",
                    special_handling="static_value",
                    extra={"value": "builtin"},
                ),
                OntologyFieldMapping(
                    ontology_field="scope",
                    node_field="scope_type",
                    special_handling="mapping",
                    extra={
                        "map": {
                            "projects": "project",
                            "organization": "org",
                            "account_root_user": "account",
                        }
                    },
                ),
            ],
        ),
    ],
)

# WorkOS
workos_mapping = OntologyMapping(
    module_name="workos",
    nodes=[
        OntologyNodeMapping(
            node_label="WorkOSRole",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                OntologyFieldMapping(
                    ontology_field="type",
                    node_field="type",
                    special_handling="mapping",
                    extra={
                        "map": {
                            "EnvironmentRole": "custom",
                            "OrganizationRole": "custom",
                        }
                    },
                ),
                OntologyFieldMapping(
                    ontology_field="scope",
                    node_field="type",
                    special_handling="mapping",
                    extra={
                        "map": {
                            "EnvironmentRole": "global",
                            "OrganizationRole": "org",
                        }
                    },
                ),
            ],
        ),
    ],
)

ROLES_ONTOLOGY_MAPPING: dict[str, OntologyMapping] = {
    "aws": aws_mapping,
    "azure": azure_mapping,
    "gcp": gcp_mapping,
    "keycloak": keycloak_mapping,
    "kubernetes": kubernetes_mapping,
    "cloudflare": cloudflare_mapping,
    "oci": oci_mapping,
    "okta": okta_mapping,
    "scaleway": scaleway_mapping,
    "workos": workos_mapping,
}
