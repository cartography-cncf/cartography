from cartography.models.ontology.mapping.specs import OntologyFieldMapping
from cartography.models.ontology.mapping.specs import OntologyMapping
from cartography.models.ontology.mapping.specs import OntologyNodeMapping

# AWS - ElasticIPAddress
aws_eip_mapping = OntologyMapping(
    module_name="aws",
    nodes=[
        OntologyNodeMapping(
            node_label="ElasticIPAddress",
            fields=[
                OntologyFieldMapping(
                    ontology_field="ip_address", node_field="public_ip", required=True
                ),
            ],
        ),
    ],
)


# Azure - AzurePublicIPAddress
azure_pip_mapping = OntologyMapping(
    module_name="azure",
    nodes=[
        OntologyNodeMapping(
            node_label="AzurePublicIPAddress",
            fields=[
                OntologyFieldMapping(
                    ontology_field="ip_address", node_field="ip_address", required=True
                ),
            ],
        ),
    ],
)


# Scaleway - ScalewayFlexibleIp
scaleway_fip_mapping = OntologyMapping(
    module_name="scaleway",
    nodes=[
        OntologyNodeMapping(
            node_label="ScalewayFlexibleIp",
            fields=[
                OntologyFieldMapping(
                    ontology_field="ip_address", node_field="address", required=True
                ),
            ],
        ),
    ],
)


# GCP - GCPNicAccessConfig
gcp_nic_mapping = OntologyMapping(
    module_name="gcp",
    nodes=[
        OntologyNodeMapping(
            node_label="GCPNicAccessConfig",
            fields=[
                OntologyFieldMapping(
                    ontology_field="ip_address", node_field="public_ip", required=True
                ),
            ],
        ),
    ],
)


PUBLIC_IPS_ONTOLOGY_MAPPING: dict[str, OntologyMapping] = {
    "aws": aws_eip_mapping,
    "azure": azure_pip_mapping,
    "gcp": gcp_nic_mapping,
    "scaleway": scaleway_fip_mapping,
}
