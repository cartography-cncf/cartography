from cartography.models.ontology.mapping.specs import OntologyFieldMapping
from cartography.models.ontology.mapping.specs import OntologyMapping
from cartography.models.ontology.mapping.specs import OntologyNodeMapping

# SecurityIssue fields:
# title (required)
# severity
# type
# status
# first_seen
#
# CVE-related nodes (TrivyImageFinding, UbuntuCVE, CVE, AWSInspectorFinding,
# S1AppFinding, SemgrepSCAFinding, SpotlightVulnerability) are intentionally
# excluded: they are already covered by the `CVE` extra label which plays the
# ontology role for CVE-linked detections.

aws_mapping = OntologyMapping(
    module_name="aws",
    nodes=[
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

SECURITY_ISSUES_ONTOLOGY_MAPPING: dict[str, OntologyMapping] = {
    "aws": aws_mapping,
    "semgrep": semgrep_mapping,
    "azure": azure_mapping,
}
