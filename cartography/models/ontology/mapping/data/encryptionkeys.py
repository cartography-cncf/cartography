from cartography.models.ontology.mapping.specs import OntologyFieldMapping
from cartography.models.ontology.mapping.specs import OntologyMapping
from cartography.models.ontology.mapping.specs import OntologyNodeMapping

# EncryptionKey fields:
# name - Key name or identifier (required)
# key_type - Key purpose or usage type (e.g., ENCRYPT_DECRYPT, SIGN_VERIFY)
# enabled - Whether the key is enabled
# rotation_enabled - Whether automatic rotation is configured

aws_mapping = OntologyMapping(
    module_name="aws",
    nodes=[
        OntologyNodeMapping(
            node_label="KMSKey",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name",
                    node_field="arn",
                    required=True,
                ),
                OntologyFieldMapping(
                    ontology_field="key_type",
                    node_field="key_usage",
                ),
                OntologyFieldMapping(
                    ontology_field="enabled",
                    node_field="enabled",
                ),
            ],
        ),
    ],
)

gcp_mapping = OntologyMapping(
    module_name="gcp",
    nodes=[
        OntologyNodeMapping(
            node_label="GCPCryptoKey",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name",
                    node_field="name",
                    required=True,
                ),
                OntologyFieldMapping(
                    ontology_field="key_type",
                    node_field="purpose",
                ),
                OntologyFieldMapping(
                    ontology_field="enabled",
                    node_field="state",
                    special_handling="equal_boolean",
                    extra={"values": ["ENABLED"]},
                ),
                OntologyFieldMapping(
                    ontology_field="rotation_enabled",
                    node_field="rotation_period",
                    special_handling="to_boolean",
                ),
            ],
        ),
    ],
)

azure_mapping = OntologyMapping(
    module_name="azure",
    nodes=[
        OntologyNodeMapping(
            node_label="AzureKeyVaultKey",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name",
                    node_field="name",
                    required=True,
                ),
                OntologyFieldMapping(
                    ontology_field="enabled",
                    node_field="enabled",
                ),
            ],
        ),
    ],
)

ENCRYPTIONKEYS_ONTOLOGY_MAPPING: dict[str, OntologyMapping] = {
    "aws": aws_mapping,
    "gcp": gcp_mapping,
    "azure": azure_mapping,
}
