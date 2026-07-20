from cartography.models.ontology.mapping.specs import OntologyFieldMapping
from cartography.models.ontology.mapping.specs import OntologyMapping
from cartography.models.ontology.mapping.specs import OntologyNodeMapping

# SecurityIssue fields:
# title (required)
# severity - Normalized band: info, low, medium, high, critical.
# type
# status - Normalized resolution: open, fixed, ignored.
# first_seen
# The raw provider value stays on each source node's own property.
#
# CVE-related nodes are intentionally excluded: they are covered by the `CVE`
# extra label and CVE semantic mapping, which plays the ontology role for
# CVE-linked detections.

# Semgrep severity (transform upper-cases the raw value; supports both the
# low/medium/high/critical and info/warning/error vocabularies).
_SEMGREP_SEVERITY = {
    "INFO": "info",
    "WARNING": "medium",
    "ERROR": "high",
    "LOW": "low",
    "MEDIUM": "medium",
    "HIGH": "high",
    "CRITICAL": "critical",
}

# Socket.dev alert severity
_SOCKETDEV_SEVERITY = {
    "low": "low",
    "middle": "medium",
    "medium": "medium",
    "high": "high",
    "critical": "critical",
}

# Semgrep SAST finding `state`
_SEMGREP_SAST_STATUS = {
    "unresolved": "open",
    "reopened": "open",
    "fixed": "fixed",
    "removed": "fixed",
    "muted": "ignored",
}

# Semgrep SCA finding `triage_status`
_SEMGREP_SCA_STATUS = {
    "untriaged": "open",
    "reopened": "open",
    "ignored": "ignored",
}

# Semgrep Secrets finding `status` (FINDING_STATUS_ prefix already stripped -> uppercase)
_SEMGREP_SECRETS_STATUS = {
    "OPEN": "open",
    "FIXED": "fixed",
    "IGNORED": "ignored",
}

# Socket.dev alert status
_SOCKETDEV_STATUS = {
    "open": "open",
    "cleared": "ignored",
}

aws_mapping = OntologyMapping(
    module_name="aws",
    nodes=[
        OntologyNodeMapping(
            node_label="AWSGuardDutyFinding",
            fields=[
                OntologyFieldMapping(
                    ontology_field="title",
                    node_field="title",
                    required=True,
                ),
                # GuardDuty severity is a numeric float; severity_label is the
                # normalized Low/Medium/High/Critical band derived at ingest.
                OntologyFieldMapping(
                    ontology_field="severity",
                    node_field="severity_label",
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
                    special_handling="mapping",
                    extra={"map": _SEMGREP_SEVERITY},
                ),
                OntologyFieldMapping(
                    ontology_field="status",
                    node_field="state",
                    special_handling="mapping",
                    extra={"map": _SEMGREP_SAST_STATUS},
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
                    special_handling="mapping",
                    extra={"map": _SEMGREP_SEVERITY},
                ),
                OntologyFieldMapping(
                    ontology_field="status",
                    node_field="triage_status",
                    special_handling="mapping",
                    extra={"map": _SEMGREP_SCA_STATUS},
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
                    special_handling="mapping",
                    extra={"map": _SEMGREP_SEVERITY},
                ),
                OntologyFieldMapping(
                    ontology_field="type",
                    node_field="type",
                ),
                OntologyFieldMapping(
                    ontology_field="status",
                    node_field="status",
                    special_handling="mapping",
                    extra={"map": _SEMGREP_SECRETS_STATUS},
                ),
                OntologyFieldMapping(
                    ontology_field="first_seen",
                    node_field="created_at",
                ),
            ],
        ),
    ],
)

socketdev_mapping = OntologyMapping(
    module_name="socketdev",
    nodes=[
        OntologyNodeMapping(
            node_label="SocketDevAlert",
            fields=[
                OntologyFieldMapping(
                    ontology_field="title",
                    node_field="title",
                    required=True,
                ),
                OntologyFieldMapping(
                    ontology_field="severity",
                    node_field="severity",
                    special_handling="mapping",
                    extra={"map": _SOCKETDEV_SEVERITY},
                ),
                OntologyFieldMapping(
                    ontology_field="type",
                    node_field="type",
                ),
                OntologyFieldMapping(
                    ontology_field="status",
                    node_field="status",
                    special_handling="mapping",
                    extra={"map": _SOCKETDEV_STATUS},
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
    "socketdev": socketdev_mapping,
    "azure": azure_mapping,
}
