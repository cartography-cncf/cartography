from cartography.models.ontology.mapping.specs import OntologyFieldMapping
from cartography.models.ontology.mapping.specs import OntologyMapping
from cartography.models.ontology.mapping.specs import OntologyNodeMapping

# Subnet fields:
# _ont_name - The name/identifier of the subnet
# _ont_cidr_block - The IP range (CIDR) of the subnet
# _ont_availability_zone - The availability zone the subnet lives in (when applicable)
# _ont_region - The region/zone where the subnet lives
#
# _ont_is_public is intentionally not mapped: no provider stores a faithful
# public/private flag on the subnet itself. Whether a subnet is public depends
# on its route table (an internet-gateway default route on AWS) or its NSG/route
# configuration (Azure), which requires a separate analysis pass to determine.

aws_mapping = OntologyMapping(
    module_name="aws",
    nodes=[
        OntologyNodeMapping(
            node_label="AWSEC2Subnet",
            fields=[
                # EC2 subnets have no display name; the SubnetId (`id`) is the
                # canonical identifier (the `name` property holds the CIDR block).
                OntologyFieldMapping(
                    ontology_field="name", node_field="id", required=True
                ),
                OntologyFieldMapping(
                    ontology_field="cidr_block", node_field="cidr_block"
                ),
                OntologyFieldMapping(
                    ontology_field="availability_zone",
                    node_field="availability_zone",
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
            node_label="GCPSubnet",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                OntologyFieldMapping(
                    ontology_field="cidr_block", node_field="ip_cidr_range"
                ),
                # _ont_availability_zone: not mapped. GCP subnets are regional, not
                # zonal, so there is no availability zone to expose.
                OntologyFieldMapping(ontology_field="region", node_field="region"),
            ],
        ),
    ],
)

azure_mapping = OntologyMapping(
    module_name="azure",
    nodes=[
        OntologyNodeMapping(
            node_label="AzureSubnet",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                OntologyFieldMapping(
                    ontology_field="cidr_block", node_field="address_prefix"
                ),
                # _ont_availability_zone: not mapped. Azure subnets are not
                # zone-scoped.
                # _ont_region: not mapped. The region/location is stored on the
                # parent AzureVirtualNetwork, not on the subnet node.
            ],
        ),
    ],
)

scaleway_mapping = OntologyMapping(
    module_name="scaleway",
    nodes=[
        OntologyNodeMapping(
            node_label="ScalewaySubnet",
            fields=[
                # Scaleway subnets have no display name; the id is the canonical
                # identifier (the `subnet` property holds the CIDR block).
                OntologyFieldMapping(
                    ontology_field="name", node_field="id", required=True
                ),
                OntologyFieldMapping(ontology_field="cidr_block", node_field="subnet"),
                # _ont_availability_zone / _ont_region: not mapped. Scaleway subnets
                # are regional and the region lives on the parent VPC / private
                # network, not on the subnet node.
            ],
        ),
    ],
)

SUBNETS_ONTOLOGY_MAPPING: dict[str, OntologyMapping] = {
    "aws": aws_mapping,
    "gcp": gcp_mapping,
    "azure": azure_mapping,
    "scaleway": scaleway_mapping,
}
