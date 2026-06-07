from cartography.models.ontology.mapping.specs import OntologyFieldMapping
from cartography.models.ontology.mapping.specs import OntologyMapping
from cartography.models.ontology.mapping.specs import OntologyNodeMapping

# DNSZone fields:
# name - The DNS zone name / domain (REQUIRED)
# public - Whether the zone is publicly accessible

# AWS
aws_mapping = OntologyMapping(
    module_name="aws",
    nodes=[
        OntologyNodeMapping(
            node_label="AWSDNSZone",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                OntologyFieldMapping(
                    ontology_field="public",
                    node_field="privatezone",
                    special_handling="invert_boolean",
                ),
            ],
        ),
    ],
)

# GCP
gcp_mapping = OntologyMapping(
    module_name="gcp",
    nodes=[
        OntologyNodeMapping(
            node_label="GCPDNSZone",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="dns_name", required=True
                ),
                OntologyFieldMapping(
                    ontology_field="public",
                    node_field="visibility",
                    special_handling="equal_boolean",
                    extra={"values": ["public"]},
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
            node_label="CloudflareZone",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                OntologyFieldMapping(
                    ontology_field="public",
                    node_field="",
                    special_handling="static_value",
                    extra={"value": True},
                ),
            ],
        ),
    ],
)

DNSZONES_ONTOLOGY_MAPPING: dict[str, OntologyMapping] = {
    "aws": aws_mapping,
    "gcp": gcp_mapping,
    "cloudflare": cloudflare_mapping,
}
