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
# Pure CVE nodes are intentionally excluded: they are covered by the `CVE`
# extra label and CVE semantic mapping, which plays the ontology role for
# CVE-linked detections. The one exception is SemgrepSCAFinding, a hybrid that is
# :SecurityIssue when advisory-only and :CVE when CVE-backed; its single mapping
# lives here and additionally carries the CVE fields (see its node mapping below).

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

# Wiz issue and finding severity/status.
_WIZ_SEVERITY = {
    "NONE": "info",
    "INFORMATIONAL": "info",
    "LOW": "low",
    "MEDIUM": "medium",
    "HIGH": "high",
    "CRITICAL": "critical",
}
_WIZ_STATUS = {
    "OPEN": "open",
    "IN_PROGRESS": "open",
    "RESOLVED": "fixed",
    "REJECTED": "ignored",
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
        # SemgrepSCAFinding is a hybrid dependency-vulnerability finding: it carries
        # :CVE when CVE-backed and :SecurityIssue when advisory-only. The resolver
        # returns a single mapping per primary label regardless of which conditional
        # label is applied, so this one mapping carries BOTH the SecurityIssue fields
        # and the CVE fields. Label-gated queries only read the fields relevant to the
        # label actually present, so the other set is inert.
        OntologyNodeMapping(
            node_label="SemgrepSCAFinding",
            fields=[
                # SecurityIssue fields (advisory-only findings)
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
                # CVE fields (CVE-backed findings)
                OntologyFieldMapping(ontology_field="cve_id", node_field="cve_id"),
                OntologyFieldMapping(
                    ontology_field="description",
                    node_field="description",
                    indexed=False,
                ),
                OntologyFieldMapping(
                    ontology_field="references",
                    node_field="ref_urls",
                    indexed=False,
                ),
                OntologyFieldMapping(
                    ontology_field="base_severity",
                    node_field="severity",
                    special_handling="mapping",
                    extra={"map": _SEMGREP_SEVERITY},
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

wiz_mapping = OntologyMapping(
    module_name="wiz",
    nodes=[
        OntologyNodeMapping(
            node_label="WizIssue",
            fields=[
                OntologyFieldMapping(
                    ontology_field="title", node_field="name", required=True
                ),
                OntologyFieldMapping(
                    ontology_field="severity",
                    node_field="severity",
                    special_handling="mapping",
                    extra={"map": _WIZ_SEVERITY},
                ),
                OntologyFieldMapping(ontology_field="type", node_field="issue_type"),
                OntologyFieldMapping(
                    ontology_field="status",
                    node_field="status",
                    special_handling="mapping",
                    extra={"map": _WIZ_STATUS},
                ),
                OntologyFieldMapping(
                    ontology_field="first_seen", node_field="created_at"
                ),
            ],
        ),
        OntologyNodeMapping(
            node_label="WizFinding",
            fields=[
                # Wiz findings are either CVE-backed vulnerabilities or non-CVE
                # security issues. The resolver returns this mapping by primary
                # label, so it carries fields for both conditional ontology labels.
                OntologyFieldMapping(
                    ontology_field="title", node_field="name", required=True
                ),
                OntologyFieldMapping(
                    ontology_field="severity",
                    node_field="severity",
                    special_handling="mapping",
                    extra={"map": _WIZ_SEVERITY},
                ),
                OntologyFieldMapping(ontology_field="type", node_field="finding_type"),
                OntologyFieldMapping(
                    ontology_field="status",
                    node_field="status",
                    special_handling="mapping",
                    extra={"map": _WIZ_STATUS},
                ),
                OntologyFieldMapping(
                    ontology_field="first_seen",
                    node_field="first_seen_at",
                    special_handling="coalesce",
                    extra={"fields": ["first_detected_at", "created_at"]},
                ),
                OntologyFieldMapping(ontology_field="cve_id", node_field="cve_id"),
                OntologyFieldMapping(
                    ontology_field="description",
                    node_field="cve_description",
                    indexed=False,
                ),
                OntologyFieldMapping(ontology_field="base_score", node_field="score"),
                OntologyFieldMapping(
                    ontology_field="base_severity",
                    node_field="cvss_severity",
                    special_handling="mapping",
                    extra={"map": _WIZ_SEVERITY},
                ),
                OntologyFieldMapping(
                    ontology_field="exploitability_score",
                    node_field="exploitability_score",
                ),
                OntologyFieldMapping(
                    ontology_field="impact_score", node_field="impact_score"
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

# Supabase security advisor lint level
_SUPABASE_ADVISOR_SEVERITY = {
    "ERROR": "high",
    "WARN": "medium",
    "INFO": "info",
}

supabase_mapping = OntologyMapping(
    module_name="supabase",
    nodes=[
        OntologyNodeMapping(
            node_label="SupabaseSecurityAdvisorFinding",
            fields=[
                OntologyFieldMapping(
                    ontology_field="title", node_field="title", required=True
                ),
                OntologyFieldMapping(ontology_field="type", node_field="name"),
                OntologyFieldMapping(
                    ontology_field="severity",
                    node_field="level",
                    special_handling="mapping",
                    extra={"map": _SUPABASE_ADVISOR_SEVERITY},
                ),
                # status: The advisor reports only currently-failing lints, so
                # every finding is implicitly open and there is no field to map.
                # first_seen: Not available.
            ],
        ),
    ],
)

SECURITY_ISSUES_ONTOLOGY_MAPPING: dict[str, OntologyMapping] = {
    "aws": aws_mapping,
    "semgrep": semgrep_mapping,
    "socketdev": socketdev_mapping,
    "wiz": wiz_mapping,
    "azure": azure_mapping,
    "supabase": supabase_mapping,
}
