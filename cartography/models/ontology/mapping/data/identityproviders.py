from cartography.models.ontology.mapping.specs import OntologyFieldMapping
from cartography.models.ontology.mapping.specs import OntologyMapping
from cartography.models.ontology.mapping.specs import OntologyNodeMapping

# IdentityProvider fields:
# _ont_name - The display name of the identity provider
# _ont_protocol - The federation protocol ("SAML", "OIDC", or provider-defined)
# _ont_issuer - The issuer URL or trust identifier
# _ont_enabled - Whether the provider is currently active

aws_mapping = OntologyMapping(
    module_name="aws",
    nodes=[
        OntologyNodeMapping(
            node_label="AWSSAMLProvider",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                OntologyFieldMapping(
                    ontology_field="protocol",
                    node_field="",
                    special_handling="static_value",
                    extra={"value": "SAML"},
                ),
                # _ont_issuer: not mapped. The AWS IAM SAML provider ARN identifies the
                # AWS-local resource, not the SAML issuer / entity ID. The real issuer lives
                # inside the SAML metadata XML returned by `GetSAMLProvider`, which we do not
                # currently parse. Mapping the ARN here would make cross-provider issuer
                # queries compare two different concepts.
                # _ont_enabled: AWS SAML providers have no enable/disable state.
            ],
        ),
    ],
)

kubernetes_mapping = OntologyMapping(
    module_name="kubernetes",
    nodes=[
        OntologyNodeMapping(
            node_label="KubernetesOIDCProvider",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                OntologyFieldMapping(
                    ontology_field="protocol",
                    node_field="",
                    special_handling="static_value",
                    extra={"value": "OIDC"},
                ),
                OntologyFieldMapping(ontology_field="issuer", node_field="issuer_url"),
                OntologyFieldMapping(
                    ontology_field="enabled",
                    node_field="status",
                    special_handling="equal_boolean",
                    extra={
                        "values": [
                            "ACTIVE",
                            "Active",
                            "active",
                            "HEALTHY",
                            "Healthy",
                            "healthy",
                        ]
                    },
                ),
            ],
        ),
    ],
)

keycloak_mapping = OntologyMapping(
    module_name="keycloak",
    nodes=[
        OntologyNodeMapping(
            node_label="KeycloakIdentityProvider",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="alias", required=True
                ),
                OntologyFieldMapping(
                    ontology_field="protocol", node_field="provider_id"
                ),
                # _ont_issuer: issuer URL lives in `config.idpEntityId` which is not stored on the node.
                OntologyFieldMapping(ontology_field="enabled", node_field="enabled"),
            ],
        ),
    ],
)

IDENTITYPROVIDERS_ONTOLOGY_MAPPING: dict[str, OntologyMapping] = {
    "aws": aws_mapping,
    "kubernetes": kubernetes_mapping,
    "keycloak": keycloak_mapping,
}
