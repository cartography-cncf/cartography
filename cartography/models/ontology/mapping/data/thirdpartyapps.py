from cartography.models.ontology.mapping.specs import OntologyFieldMapping
from cartography.models.ontology.mapping.specs import OntologyMapping
from cartography.models.ontology.mapping.specs import OntologyNodeMapping

# ThirdPartyApp ontology fields:
# client_id (REQUIRED) - OAuth client identifier
# name (REQUIRED) - Display name of the third-party application
# enabled - Whether the third-party app is enabled/active
# native_app - Whether this is a native application (vs web)
# protocol - OAuth protocol type (oauth2, openid-connect, saml, etc.)

googleworkspace_mapping = OntologyMapping(
    module_name="googleworkspace",
    nodes=[
        OntologyNodeMapping(
            node_label="GoogleWorkspaceOAuthApp",
            fields=[
                OntologyFieldMapping(
                    ontology_field="client_id",
                    node_field="client_id",
                    required=True,
                ),
                OntologyFieldMapping(
                    ontology_field="name",
                    node_field="display_text",
                    required=True,
                ),
                # enabled: Not available - Google Workspace third-party apps don't have an enabled/disabled state
                OntologyFieldMapping(
                    ontology_field="native_app",
                    node_field="native_app",
                ),
                OntologyFieldMapping(
                    ontology_field="protocol",
                    node_field="",
                    special_handling="static_value",
                    extra={"value": "oauth2"},
                ),
            ],
        ),
    ],
)

keycloak_mapping = OntologyMapping(
    module_name="keycloak",
    nodes=[
        OntologyNodeMapping(
            node_label="KeycloakClient",
            fields=[
                OntologyFieldMapping(
                    ontology_field="client_id",
                    node_field="client_id",
                    required=True,
                ),
                OntologyFieldMapping(
                    ontology_field="name",
                    node_field="name",
                    required=True,
                ),
                OntologyFieldMapping(
                    ontology_field="enabled",
                    node_field="enabled",
                ),
                # native_app: Not available - Keycloak doesn't distinguish native vs web apps in this field
                OntologyFieldMapping(
                    ontology_field="protocol",
                    node_field="protocol",
                ),
            ],
        ),
    ],
)

entra_mapping = OntologyMapping(
    module_name="entra",
    nodes=[
        OntologyNodeMapping(
            node_label="EntraApplication",
            fields=[
                OntologyFieldMapping(
                    ontology_field="client_id",
                    node_field="app_id",
                    required=True,
                ),
                OntologyFieldMapping(
                    ontology_field="name",
                    node_field="display_name",
                    required=True,
                ),
                # enabled: Not available - Entra applications don't have an enabled field in current schema
                # native_app: Not available - Application type not currently ingested
                OntologyFieldMapping(
                    ontology_field="protocol",
                    node_field="",
                    special_handling="static_value",
                    extra={"value": "oauth2"},
                ),
            ],
        ),
    ],
)

okta_mapping = OntologyMapping(
    module_name="okta",
    nodes=[
        OntologyNodeMapping(
            node_label="OktaApplication",
            fields=[
                OntologyFieldMapping(
                    ontology_field="client_id",
                    node_field="id",  # Note: This is Okta's internal app ID, not OAuth client_id
                    required=True,
                ),
                OntologyFieldMapping(
                    ontology_field="name",
                    node_field="label",
                    required=True,
                ),
                OntologyFieldMapping(
                    ontology_field="enabled",
                    node_field="status",
                    extra={"values": ["ACTIVE"]},
                    special_handling="equal_boolean",
                ),
                # native_app: Not available - Application type not distinguished in current schema
                OntologyFieldMapping(
                    ontology_field="protocol",
                    node_field="sign_on_mode",
                ),
            ],
        ),
    ],
)

THIRDPARTYAPPS_ONTOLOGY_MAPPING: dict[str, OntologyMapping] = {
    "googleworkspace": googleworkspace_mapping,
    "keycloak": keycloak_mapping,
    "entra": entra_mapping,
    "okta": okta_mapping,
}
