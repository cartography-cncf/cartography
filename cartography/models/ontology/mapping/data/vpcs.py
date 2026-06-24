from cartography.models.ontology.mapping.specs import OntologyFieldMapping
from cartography.models.ontology.mapping.specs import OntologyMapping
from cartography.models.ontology.mapping.specs import OntologyNodeMapping

# VirtualNetwork fields:
# _ont_name - The name/identifier of the virtual network
# _ont_cidr - The IP range (CIDR) of the virtual network, when the provider
#             exposes it at the network level
# _ont_region - The region where the virtual network lives, when applicable

aws_mapping = OntologyMapping(
    module_name="aws",
    nodes=[
        OntologyNodeMapping(
            node_label="AWSVpc",
            fields=[
                # AWS VPCs have no display name; the VpcId (`id`) is the
                # canonical identifier.
                OntologyFieldMapping(
                    ontology_field="name", node_field="id", required=True
                ),
                OntologyFieldMapping(
                    ontology_field="cidr", node_field="primary_cidr_block"
                ),
                OntologyFieldMapping(ontology_field="region", node_field="region"),
            ],
        ),
    ],
)

gcp_mapping = OntologyMapping(
    module_name="gcp",
    nodes=[
        OntologyNodeMapping(
            node_label="GCPVpc",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                # _ont_cidr: not mapped. GCP VPCs do not carry a CIDR block; the IP
                # ranges live on the member subnetworks (GCPSubnet.ip_cidr_range).
                # _ont_region: not mapped. GCP VPCs are global, not regional.
            ],
        ),
    ],
)

azure_mapping = OntologyMapping(
    module_name="azure",
    nodes=[
        OntologyNodeMapping(
            node_label="AzureVirtualNetwork",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                # _ont_cidr: not mapped. The address space is not captured on the
                # AzureVirtualNetwork node; CIDRs live on the member AzureSubnet
                # (address_prefix).
                OntologyFieldMapping(ontology_field="region", node_field="location"),
            ],
        ),
    ],
)

VPCS_ONTOLOGY_MAPPING: dict[str, OntologyMapping] = {
    "aws": aws_mapping,
    "gcp": gcp_mapping,
    "azure": azure_mapping,
}
