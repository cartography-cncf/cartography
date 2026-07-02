from cartography.models.ontology.mapping.specs import OntologyFieldMapping
from cartography.models.ontology.mapping.specs import OntologyMapping
from cartography.models.ontology.mapping.specs import OntologyNodeMapping

# CVE fields:
# cve_id
# assigner
# description
# references
# problem_types
# vector_string
# attack_vector
# attack_complexity
# privileges_required
# user_interaction
# scope
# confidentiality_impact
# integrity_impact
# availability_impact
# base_score
# base_severity
# exploitability_score
# impact_score
# published_date
# last_modified_date
# vuln_status

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
