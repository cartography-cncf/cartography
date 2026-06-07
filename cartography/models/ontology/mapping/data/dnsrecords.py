from cartography.models.ontology.mapping.specs import OntologyFieldMapping
from cartography.models.ontology.mapping.specs import OntologyMapping
from cartography.models.ontology.mapping.specs import OntologyNodeMapping

# DNSRecord fields:
# name - The DNS record hostname (REQUIRED)
# type - The DNS record type (A, AAAA, CNAME, MX, TXT, etc.)
# value - The DNS record value / target (IP address, CNAME target, etc.)

# AWS
aws_mapping = OntologyMapping(
    module_name="aws",
    nodes=[
        OntologyNodeMapping(
            node_label="AWSDNSRecord",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                OntologyFieldMapping(ontology_field="type", node_field="type"),
                OntologyFieldMapping(ontology_field="value", node_field="value"),
            ],
        ),
    ],
)

# GCP
gcp_mapping = OntologyMapping(
    module_name="gcp",
    nodes=[
        OntologyNodeMapping(
            node_label="GCPRecordSet",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                OntologyFieldMapping(ontology_field="type", node_field="type"),
                OntologyFieldMapping(ontology_field="value", node_field="data"),
            ],
        ),
    ],
)

# Cloudflare
cloudflare_mapping = OntologyMapping(
    module_name="cloudflare",
    nodes=[
        OntologyNodeMapping(
            node_label="CloudflareDNSRecord",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                OntologyFieldMapping(ontology_field="type", node_field="type"),
                OntologyFieldMapping(ontology_field="value", node_field="value"),
            ],
        ),
    ],
)

# Vercel
vercel_mapping = OntologyMapping(
    module_name="vercel",
    nodes=[
        OntologyNodeMapping(
            node_label="VercelDNSRecord",
            fields=[
                OntologyFieldMapping(
                    ontology_field="name", node_field="name", required=True
                ),
                OntologyFieldMapping(ontology_field="type", node_field="type"),
                OntologyFieldMapping(ontology_field="value", node_field="value"),
            ],
        ),
    ],
)

DNSRECORDS_ONTOLOGY_MAPPING: dict[str, OntologyMapping] = {
    "aws": aws_mapping,
    "gcp": gcp_mapping,
    "cloudflare": cloudflare_mapping,
    "vercel": vercel_mapping,
}
