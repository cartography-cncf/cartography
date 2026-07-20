from cartography.models.ontology.mapping.specs import OntologyFieldMapping
from cartography.models.ontology.mapping.specs import OntologyMapping
from cartography.models.ontology.mapping.specs import OntologyNodeMapping

# CVE fields:
# cve_id, assigner, description, references, problem_types, vector_string,
# attack_vector, attack_complexity, privileges_required, user_interaction, scope,
# confidentiality_impact, integrity_impact, availability_impact, base_score,
# exploitability_score, impact_score, published_date, last_modified_date
#
# Normalized fields:
# base_severity - canonical severity band: info, low, medium, high, critical.
# vuln_status - canonical resolution state: open, fixed, rejected,
#   under_investigation, not_affected, unknown.
# The raw provider value stays on each source node's own property.

# CVSS v3 baseSeverity (also covers Trivy/Crowdstrike uppercase severity subsets)
_CVSS_SEVERITY = {
    "NONE": "info",
    "LOW": "low",
    "MEDIUM": "medium",
    "HIGH": "high",
    "CRITICAL": "critical",
}

# GitHub GraphQL severity (uppercase API + lowercase fixture variants)
_GITHUB_SEVERITY = {
    "LOW": "low",
    "MODERATE": "medium",
    "HIGH": "high",
    "CRITICAL": "critical",
    "low": "low",
    "moderate": "medium",
    "medium": "medium",
    "high": "high",
    "critical": "critical",
}

# SentinelOne severity (title case)
_S1_SEVERITY = {
    "None": "info",
    "Low": "low",
    "Medium": "medium",
    "High": "high",
    "Critical": "critical",
}

# NVD vulnStatus -> resolution state. NVD's values are analysis-workflow states; all
# non-rejected ones mean the record is live, so they collapse to "open".
_NVD_VULN_STATUS = {
    "Received": "open",
    "Awaiting Analysis": "open",
    "Undergoing Analysis": "open",
    "Analyzed": "open",
    "Modified": "open",
    "Deferred": "open",
    "Rejected": "rejected",
}

# Trivy vulnerability Status
_TRIVY_VULN_STATUS = {
    "unknown": "unknown",
    "affected": "open",
    "fixed": "fixed",
    "under_investigation": "under_investigation",
    "will_not_fix": "not_affected",
    "fix_deferred": "open",
    "end_of_life": "open",
    "not_affected": "not_affected",
}

# Ubuntu CVE tracking status
_UBUNTU_VULN_STATUS = {
    "active": "open",
    "rejected": "rejected",
    "not-in-ubuntu": "not_affected",
}

cve_mapping = OntologyMapping(
    module_name="cve",
    nodes=[
        OntologyNodeMapping(
            node_label="CVE",
            fields=[
                OntologyFieldMapping(ontology_field="cve_id", node_field="cve_id"),
                OntologyFieldMapping(ontology_field="assigner", node_field="assigner"),
                OntologyFieldMapping(
                    ontology_field="description",
                    node_field="description",
                    indexed=False,
                ),
                OntologyFieldMapping(
                    ontology_field="references",
                    node_field="references",
                    indexed=False,
                ),
                OntologyFieldMapping(
                    ontology_field="problem_types",
                    node_field="problem_types",
                    indexed=False,
                ),
                OntologyFieldMapping(
                    ontology_field="vector_string",
                    node_field="vector_string",
                ),
                OntologyFieldMapping(
                    ontology_field="attack_vector",
                    node_field="attack_vector",
                ),
                OntologyFieldMapping(
                    ontology_field="attack_complexity",
                    node_field="attack_complexity",
                ),
                OntologyFieldMapping(
                    ontology_field="privileges_required",
                    node_field="privileges_required",
                ),
                OntologyFieldMapping(
                    ontology_field="user_interaction",
                    node_field="user_interaction",
                ),
                OntologyFieldMapping(ontology_field="scope", node_field="scope"),
                OntologyFieldMapping(
                    ontology_field="confidentiality_impact",
                    node_field="confidentiality_impact",
                ),
                OntologyFieldMapping(
                    ontology_field="integrity_impact",
                    node_field="integrity_impact",
                ),
                OntologyFieldMapping(
                    ontology_field="availability_impact",
                    node_field="availability_impact",
                ),
                OntologyFieldMapping(
                    ontology_field="base_score",
                    node_field="base_score",
                ),
                OntologyFieldMapping(
                    ontology_field="base_severity",
                    node_field="base_severity",
                    special_handling="mapping",
                    extra={"map": _CVSS_SEVERITY},
                ),
                OntologyFieldMapping(
                    ontology_field="exploitability_score",
                    node_field="exploitability_score",
                ),
                OntologyFieldMapping(
                    ontology_field="impact_score",
                    node_field="impact_score",
                ),
                OntologyFieldMapping(
                    ontology_field="published_date",
                    node_field="published_date",
                ),
                OntologyFieldMapping(
                    ontology_field="last_modified_date",
                    node_field="last_modified_date",
                ),
                OntologyFieldMapping(
                    ontology_field="vuln_status",
                    node_field="vuln_status",
                    special_handling="mapping",
                    extra={"map": _NVD_VULN_STATUS},
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
                OntologyFieldMapping(ontology_field="cve_id", node_field="cve_id"),
                OntologyFieldMapping(
                    ontology_field="description",
                    node_field="description",
                    indexed=False,
                ),
                OntologyFieldMapping(
                    ontology_field="references",
                    node_field="references",
                    indexed=False,
                ),
                OntologyFieldMapping(
                    ontology_field="problem_types",
                    node_field="cwe_ids",
                    indexed=False,
                ),
                OntologyFieldMapping(
                    ontology_field="vector_string",
                    node_field="cvss_nvd_v3_vector",
                ),
                OntologyFieldMapping(
                    ontology_field="base_score",
                    node_field="cvss_nvd_v3_score",
                ),
                OntologyFieldMapping(
                    ontology_field="base_severity",
                    node_field="severity",
                    special_handling="mapping",
                    extra={"map": _CVSS_SEVERITY},
                ),
                OntologyFieldMapping(
                    ontology_field="published_date",
                    node_field="published_date",
                ),
                OntologyFieldMapping(
                    ontology_field="last_modified_date",
                    node_field="last_modified_date",
                ),
                OntologyFieldMapping(
                    ontology_field="vuln_status",
                    node_field="status",
                    special_handling="mapping",
                    extra={"map": _TRIVY_VULN_STATUS},
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
                OntologyFieldMapping(ontology_field="cve_id", node_field="cve_id"),
                OntologyFieldMapping(
                    ontology_field="description",
                    node_field="description",
                    indexed=False,
                ),
                OntologyFieldMapping(
                    ontology_field="attack_vector",
                    node_field="attack_vector",
                ),
                OntologyFieldMapping(
                    ontology_field="attack_complexity",
                    node_field="attack_complexity",
                ),
                OntologyFieldMapping(
                    ontology_field="confidentiality_impact",
                    node_field="confidentiality_impact",
                ),
                OntologyFieldMapping(
                    ontology_field="integrity_impact",
                    node_field="integrity_impact",
                ),
                OntologyFieldMapping(
                    ontology_field="availability_impact",
                    node_field="availability_impact",
                ),
                OntologyFieldMapping(
                    ontology_field="base_score",
                    node_field="base_score",
                ),
                OntologyFieldMapping(
                    ontology_field="base_severity",
                    node_field="base_severity",
                    special_handling="mapping",
                    extra={"map": _CVSS_SEVERITY},
                ),
                OntologyFieldMapping(
                    ontology_field="published_date",
                    node_field="published",
                ),
                OntologyFieldMapping(
                    ontology_field="last_modified_date",
                    node_field="updated_at",
                ),
                OntologyFieldMapping(
                    ontology_field="vuln_status",
                    node_field="status",
                    special_handling="mapping",
                    extra={"map": _UBUNTU_VULN_STATUS},
                ),
            ],
        ),
    ],
)

crowdstrike_mapping = OntologyMapping(
    module_name="crowdstrike",
    nodes=[
        OntologyNodeMapping(
            node_label="CrowdstrikeFinding",
            fields=[
                OntologyFieldMapping(ontology_field="cve_id", node_field="cve_id"),
                OntologyFieldMapping(
                    ontology_field="base_score",
                    node_field="base_score",
                ),
                OntologyFieldMapping(
                    ontology_field="base_severity",
                    node_field="base_severity",
                    special_handling="mapping",
                    extra={"map": _CVSS_SEVERITY},
                ),
            ],
        ),
    ],
)

github_mapping = OntologyMapping(
    module_name="github",
    nodes=[
        OntologyNodeMapping(
            node_label="GitHubDependabotAlert",
            fields=[
                OntologyFieldMapping(ontology_field="cve_id", node_field="cve_id"),
                OntologyFieldMapping(
                    ontology_field="description",
                    node_field="advisory_description",
                    indexed=False,
                ),
                OntologyFieldMapping(
                    ontology_field="references",
                    node_field="references",
                    indexed=False,
                ),
                OntologyFieldMapping(
                    ontology_field="problem_types",
                    node_field="cwe_ids",
                    indexed=False,
                ),
                OntologyFieldMapping(
                    ontology_field="vector_string",
                    node_field="cvss_vector_string",
                ),
                OntologyFieldMapping(
                    ontology_field="base_score",
                    node_field="cvss_score",
                ),
                OntologyFieldMapping(
                    ontology_field="base_severity",
                    node_field="severity",
                    special_handling="mapping",
                    extra={"map": _GITHUB_SEVERITY},
                ),
                OntologyFieldMapping(
                    ontology_field="published_date",
                    node_field="advisory_published_at",
                ),
                OntologyFieldMapping(
                    ontology_field="last_modified_date",
                    node_field="advisory_updated_at",
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
                OntologyFieldMapping(ontology_field="cve_id", node_field="cve_id"),
                OntologyFieldMapping(
                    ontology_field="base_severity",
                    node_field="severity",
                    special_handling="mapping",
                    extra={"map": _S1_SEVERITY},
                ),
            ],
        ),
    ],
)

CVES_ONTOLOGY_MAPPING: dict[str, OntologyMapping] = {
    "cve": cve_mapping,
    "trivy": trivy_mapping,
    "ubuntu": ubuntu_mapping,
    "crowdstrike": crowdstrike_mapping,
    "github": github_mapping,
    "sentinelone": sentinelone_mapping,
}
