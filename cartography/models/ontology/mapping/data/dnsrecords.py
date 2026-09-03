from cartography.models.ontology.mapping.specs import OntologyFieldMapping
from cartography.models.ontology.mapping.specs import OntologyMapping
from cartography.models.ontology.mapping.specs import OntologyNodeMapping

# DNSRecord fields:
# name - The DNS record hostname (REQUIRED)
# type - The DNS record type (A, AAAA, CNAME, MX, TXT, etc.)
# value - The DNS record value / target (IP address, CNAME target, etc.)

HOSTNAME_RECORD_TYPES = ["CNAME", "ALIAS"]


def _name_field(node_field: str = "name") -> OntologyFieldMapping:
    return OntologyFieldMapping(
        ontology_field="name",
        node_field=node_field,
        required=True,
        special_handling="normalize_hostname",
    )


def _target_hostname_field(node_field: str = "value") -> OntologyFieldMapping:
    return OntologyFieldMapping(
        ontology_field="target_hostname",
        node_field=node_field,
        special_handling="normalize_hostname",
        extra={"record_types": HOSTNAME_RECORD_TYPES},
    )


# AWS
aws_mapping = OntologyMapping(
    module_name="aws",
    nodes=[
        OntologyNodeMapping(
            node_label="AWSDNSRecord",
            fields=[
                _name_field(),
                OntologyFieldMapping(ontology_field="type", node_field="type"),
                OntologyFieldMapping(ontology_field="value", node_field="value"),
                _target_hostname_field(),
            ],
        ),
    ],
)

# GCP
# GCPRecordSet.data is list-valued, so it is not mapped to the scalar _ont_value:
# toString(_ont_value) in the DNS_RECORD_LINKING_JOBS analysis jobs rejects lists. GCP
# record linking is done directly off the raw list field via UNWIND dns.data in those jobs.
gcp_mapping = OntologyMapping(
    module_name="gcp",
    nodes=[
        OntologyNodeMapping(
            node_label="GCPRecordSet",
            fields=[
                _name_field(),
                OntologyFieldMapping(ontology_field="type", node_field="type"),
                OntologyFieldMapping(
                    ontology_field="target_hostnames",
                    node_field="target_hostnames",
                    indexed=False,
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
            node_label="CloudflareDNSRecord",
            fields=[
                _name_field(),
                OntologyFieldMapping(ontology_field="type", node_field="type"),
                OntologyFieldMapping(ontology_field="value", node_field="value"),
                _target_hostname_field(),
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
                _name_field(),
                OntologyFieldMapping(ontology_field="type", node_field="type"),
                OntologyFieldMapping(ontology_field="value", node_field="value"),
                _target_hostname_field(),
            ],
        ),
    ],
)

# BBOT
bbot_mapping = OntologyMapping(
    module_name="bbot",
    nodes=[
        OntologyNodeMapping(
            node_label="BbotDNSName",
            fields=[
                _name_field(),
            ],
        ),
    ],
)

# Supabase
supabase_mapping = OntologyMapping(
    module_name="supabase",
    nodes=[
        OntologyNodeMapping(
            node_label="SupabaseCustomHostname",
            fields=[
                _name_field("hostname"),
                OntologyFieldMapping(ontology_field="type", node_field="type"),
                # value: The CNAME target is the project's own *.supabase.co
                # endpoint, which the API does not return on this response.
            ],
        ),
    ],
)

# Netlify
netlify_mapping = OntologyMapping(
    module_name="netlify",
    nodes=[
        OntologyNodeMapping(
            node_label="NetlifyDNSRecord",
            fields=[
                _name_field(),
                OntologyFieldMapping(ontology_field="type", node_field="type"),
                OntologyFieldMapping(ontology_field="value", node_field="value"),
                _target_hostname_field(),
            ],
        ),
    ],
)

DNSRECORDS_ONTOLOGY_MAPPING: dict[str, OntologyMapping] = {
    "aws": aws_mapping,
    "gcp": gcp_mapping,
    "cloudflare": cloudflare_mapping,
    "vercel": vercel_mapping,
    "bbot": bbot_mapping,
    "supabase": supabase_mapping,
    "netlify": netlify_mapping,
}
