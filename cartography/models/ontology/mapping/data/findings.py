from cartography.models.ontology.mapping.specs import OntologyFieldMapping
from cartography.models.ontology.mapping.specs import OntologyMapping
from cartography.models.ontology.mapping.specs import OntologyNodeMapping

# Finding fields:
# title (required)
# severity
# type
# status
# first_seen

aws_mapping = OntologyMapping(
    module_name="aws",
    nodes=[
        OntologyNodeMapping(
            node_label="AWSInspectorFinding",
            fields=[
                OntologyFieldMapping(
                    ontology_field="title",
                    node_field="name",
                    required=True,
                ),
                OntologyFieldMapping(
                    ontology_field="severity",
                    node_field="severity",
                ),
                OntologyFieldMapping(
                    ontology_field="type",
                    node_field="type",
                ),
                OntologyFieldMapping(
                    ontology_field="status",
                    node_field="status",
                ),
                OntologyFieldMapping(
                    ontology_field="first_seen",
                    node_field="firstobservedat",
                ),
            ],
        ),
        OntologyNodeMapping(
            node_label="GuardDutyFinding",
            fields=[
                OntologyFieldMapping(
                    ontology_field="title",
                    node_field="title",
                    required=True,
                ),
                OntologyFieldMapping(
                    ontology_field="severity",
                    node_field="severity",
                ),
                OntologyFieldMapping(
                    ontology_field="type",
                    node_field="type",
                ),
                OntologyFieldMapping(
                    ontology_field="first_seen",
                    node_field="eventfirstseen",
                ),
            ],
        ),
    ],
)

semgrep_mapping = OntologyMapping(
    module_name="semgrep",
    nodes=[
        OntologyNodeMapping(
            node_label="SemgrepSASTFinding",
            fields=[
                OntologyFieldMapping(
                    ontology_field="title",
                    node_field="title",
                    required=True,
                ),
                OntologyFieldMapping(
                    ontology_field="severity",
                    node_field="severity",
                ),
                OntologyFieldMapping(
                    ontology_field="status",
                    node_field="state",
                ),
                OntologyFieldMapping(
                    ontology_field="first_seen",
                    node_field="opened_at",
                ),
            ],
        ),
        OntologyNodeMapping(
            node_label="SemgrepSCAFinding",
            fields=[
                OntologyFieldMapping(
                    ontology_field="title",
                    node_field="summary",
                    required=True,
                ),
                OntologyFieldMapping(
                    ontology_field="severity",
                    node_field="severity",
                ),
                OntologyFieldMapping(
                    ontology_field="status",
                    node_field="triage_status",
                ),
                OntologyFieldMapping(
                    ontology_field="first_seen",
                    node_field="scan_time",
                ),
            ],
        ),
        # SemgrepSecretsFinding has no dedicated title; type (e.g. "AWS Secret Key") serves as both
        OntologyNodeMapping(
            node_label="SemgrepSecretsFinding",
            fields=[
                OntologyFieldMapping(
                    ontology_field="title",
                    node_field="type",
                    required=True,
                ),
                OntologyFieldMapping(
                    ontology_field="severity",
                    node_field="severity",
                ),
                OntologyFieldMapping(
                    ontology_field="type",
                    node_field="type",
                ),
                OntologyFieldMapping(
                    ontology_field="status",
                    node_field="status",
                ),
                OntologyFieldMapping(
                    ontology_field="first_seen",
                    node_field="created_at",
                ),
            ],
        ),
    ],
)

cve_mapping = OntologyMapping(
    module_name="cve",
    nodes=[
        OntologyNodeMapping(
            node_label="CVE",
            fields=[
                OntologyFieldMapping(
                    ontology_field="title",
                    node_field="cve_id",
                    required=True,
                ),
                OntologyFieldMapping(
                    ontology_field="severity",
                    node_field="base_severity",
                ),
                OntologyFieldMapping(
                    ontology_field="status",
                    node_field="vuln_status",
                ),
                OntologyFieldMapping(
                    ontology_field="first_seen",
                    node_field="published_date",
                ),
            ],
        ),
    ],
)

sentinelone_mapping = OntologyMapping(
    module_name="sentinelone",
    nodes=[
        OntologyNodeMapping(
            node_label="S1AppFinding",
            fields=[
                OntologyFieldMapping(
                    ontology_field="title",
                    node_field="cve_id",
                    required=True,
                ),
                OntologyFieldMapping(
                    ontology_field="severity",
                    node_field="severity",
                ),
                OntologyFieldMapping(
                    ontology_field="status",
                    node_field="status",
                ),
                OntologyFieldMapping(
                    ontology_field="first_seen",
                    node_field="detection_date",
                ),
            ],
        ),
    ],
)

trivy_mapping = OntologyMapping(
    module_name="trivy",
    nodes=[
        OntologyNodeMapping(
            node_label="TrivyImageFinding",
            fields=[
                OntologyFieldMapping(
                    ontology_field="title",
                    node_field="title",
                    required=True,
                ),
                OntologyFieldMapping(
                    ontology_field="severity",
                    node_field="severity",
                ),
                OntologyFieldMapping(
                    ontology_field="type",
                    node_field="type",
                ),
                OntologyFieldMapping(
                    ontology_field="status",
                    node_field="status",
                ),
                OntologyFieldMapping(
                    ontology_field="first_seen",
                    node_field="published_date",
                ),
            ],
        ),
    ],
)

azure_mapping = OntologyMapping(
    module_name="azure",
    nodes=[
        OntologyNodeMapping(
            node_label="AzureSecurityAssessment",
            fields=[
                OntologyFieldMapping(
                    ontology_field="title",
                    node_field="display_name",
                    required=True,
                ),
            ],
        ),
    ],
)

ubuntu_mapping = OntologyMapping(
    module_name="ubuntu",
    nodes=[
        OntologyNodeMapping(
            node_label="UbuntuCVE",
            fields=[
                OntologyFieldMapping(
                    ontology_field="title",
                    node_field="cve_id",
                    required=True,
                ),
                OntologyFieldMapping(
                    ontology_field="severity",
                    node_field="base_severity",
                ),
                OntologyFieldMapping(
                    ontology_field="status",
                    node_field="status",
                ),
                OntologyFieldMapping(
                    ontology_field="first_seen",
                    node_field="published",
                ),
            ],
        ),
    ],
)

# Note: SpotlightVulnerability (crowdstrike) uses raw Cypher ingestion
# and does not have a CartographyNodeSchema. Its Finding label and _ont_*
# properties are set directly in cartography/intel/crowdstrike/spotlight.py.

FINDINGS_ONTOLOGY_MAPPING: dict[str, OntologyMapping] = {
    "aws": aws_mapping,
    "semgrep": semgrep_mapping,
    "cve": cve_mapping,
    "sentinelone": sentinelone_mapping,
    "trivy": trivy_mapping,
    "azure": azure_mapping,
    "ubuntu": ubuntu_mapping,
}
