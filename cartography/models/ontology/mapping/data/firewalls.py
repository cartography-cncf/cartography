from cartography.models.ontology.mapping.specs import OntologyFieldMapping
from cartography.models.ontology.mapping.specs import OntologyMapping
from cartography.models.ontology.mapping.specs import OntologyNodeMapping

# NetworkAccessControl fields:
# name - Display name of the security group or firewall (REQUIRED)
# direction - Traffic direction (inbound/outbound), if applicable

# AWS
aws_mapping = OntologyMapping(
    module_name="aws",
    nodes=[
        OntologyNodeMapping(
            node_label="EC2SecurityGroup",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                # direction: intentionally not projected. AWS security groups
                # are bidirectional containers and almost always carry both
                # ingress and egress rules at the same time, so a single
                # direction value at the SG level would be uniformly "BOTH"
                # and not useful for cross-cloud correlation. Direction lives
                # on the individual IpPermissionInbound / IpPermissionEgress
                # rule nodes instead.
            ],
        ),
    ],
)

# GCP
gcp_mapping = OntologyMapping(
    module_name="gcp",
    nodes=[
        OntologyNodeMapping(
            node_label="GCPFirewall",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                OntologyFieldMapping(
                    ontology_field="direction", node_field="direction"
                ),
            ],
        ),
        OntologyNodeMapping(
            node_label="GCPCloudArmorPolicy",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                # direction: Not applicable (Cloud Armor applies to inbound traffic)
            ],
        ),
    ],
)

# Azure
azure_mapping = OntologyMapping(
    module_name="azure",
    nodes=[
        OntologyNodeMapping(
            node_label="AzureNetworkSecurityGroup",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                # direction: Not applicable (NSGs are bidirectional)
            ],
        ),
        OntologyNodeMapping(
            node_label="AzureFirewall",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                # direction: Not applicable (bidirectional)
            ],
        ),
    ],
)

FIREWALLS_ONTOLOGY_MAPPING: dict[str, OntologyMapping] = {
    "aws": aws_mapping,
    "gcp": gcp_mapping,
    "azure": azure_mapping,
}
