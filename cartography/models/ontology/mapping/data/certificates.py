from cartography.models.ontology.mapping.specs import OntologyFieldMapping
from cartography.models.ontology.mapping.specs import OntologyMapping
from cartography.models.ontology.mapping.specs import OntologyNodeMapping

# Certificate fields:
# domain - Domain name or certificate name (REQUIRED)
# expiry - Expiration date/time
# issuer - Certificate issuer

# AWS (ACM Certificate + IAM Server Certificate)
aws_mapping = OntologyMapping(
    module_name="aws",
    nodes=[
        OntologyNodeMapping(
            node_label="ACMCertificate",
            fields=[
                OntologyFieldMapping(
                    ontology_field="domain", node_field="domainname", required=True
                ),
                OntologyFieldMapping(ontology_field="expiry", node_field="not_after"),
                # issuer: Not available
            ],
        ),
        OntologyNodeMapping(
            node_label="AWSServerCertificate",
            fields=[
                OntologyFieldMapping(
                    ontology_field="domain",
                    node_field="server_certificate_name",
                    required=True,
                ),
                OntologyFieldMapping(ontology_field="expiry", node_field="expiration"),
                # issuer: Not available
            ],
        ),
    ],
)

# Azure Key Vault Certificate
azure_mapping = OntologyMapping(
    module_name="azure",
    nodes=[
        OntologyNodeMapping(
            node_label="AzureKeyVaultCertificate",
            fields=[
                OntologyFieldMapping(
                    ontology_field="domain", node_field="name", required=True
                ),
                # expiry: Not available
                # issuer: Not available
            ],
        ),
    ],
)

CERTIFICATES_ONTOLOGY_MAPPING: dict[str, OntologyMapping] = {
    "aws": aws_mapping,
    "azure": azure_mapping,
}
