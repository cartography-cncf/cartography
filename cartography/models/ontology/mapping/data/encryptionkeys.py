from cartography.models.ontology.mapping.specs import OntologyFieldMapping
from cartography.models.ontology.mapping.specs import OntologyMapping
from cartography.models.ontology.mapping.specs import OntologyNodeMapping

# EncryptionKey fields:
# name - Key name or identifier (required)
# key_type - Key purpose/usage, normalized to the shared canonical set:
#   encrypt_decrypt, sign_verify, asymmetric_sign, asymmetric_decrypt, mac,
#   key_agreement, key_encapsulation.
#   The raw provider value stays on the source node's own key_usage/purpose/usage_type property.
# enabled - Whether the key is enabled
# rotation_enabled - Whether automatic rotation is configured

# AWS KMS KeyUsage
_AWS_KMS_KEY_TYPE = {
    "ENCRYPT_DECRYPT": "encrypt_decrypt",
    "SIGN_VERIFY": "sign_verify",
    "GENERATE_VERIFY_MAC": "mac",
    "KEY_AGREEMENT": "key_agreement",
}

# GCP CryptoKeyPurpose
_GCP_CRYPTOKEY_TYPE = {
    "ENCRYPT_DECRYPT": "encrypt_decrypt",
    "RAW_ENCRYPT_DECRYPT": "encrypt_decrypt",
    "ASYMMETRIC_SIGN": "asymmetric_sign",
    "ASYMMETRIC_DECRYPT": "asymmetric_decrypt",
    "MAC": "mac",
    "KEY_ENCAPSULATION": "key_encapsulation",
}

# Scaleway KMS key usage (one-of holder field name)
_SCALEWAY_KEY_TYPE = {
    "symmetric_encryption": "encrypt_decrypt",
    "asymmetric_encryption": "asymmetric_decrypt",
    "asymmetric_signing": "asymmetric_sign",
}

aws_mapping = OntologyMapping(
    module_name="aws",
    nodes=[
        OntologyNodeMapping(
            node_label="AWSKMSKey",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name",
                    node_field="arn",
                    required=True,
                ),
                OntologyFieldMapping(
                    ontology_field="key_type",
                    node_field="key_usage",
                    special_handling="mapping",
                    extra={"map": _AWS_KMS_KEY_TYPE},
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
                    special_handling="mapping",
                    extra={"map": _GCP_CRYPTOKEY_TYPE},
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

scaleway_mapping = OntologyMapping(
    module_name="scaleway",
    nodes=[
        OntologyNodeMapping(
            node_label="ScalewayKey",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name",
                    node_field="name",
                    required=True,
                ),
                OntologyFieldMapping(
                    ontology_field="key_type",
                    node_field="usage_type",
                    special_handling="mapping",
                    extra={"map": _SCALEWAY_KEY_TYPE},
                ),
                OntologyFieldMapping(
                    ontology_field="enabled",
                    node_field="state",
                    special_handling="equal_boolean",
                    extra={"values": ["enabled"]},
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

ENCRYPTIONKEYS_ONTOLOGY_MAPPING: dict[str, OntologyMapping] = {
    "aws": aws_mapping,
    "gcp": gcp_mapping,
    "azure": azure_mapping,
    "scaleway": scaleway_mapping,
}
