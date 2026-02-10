"""Ontology field mappings for vulnerability data.

Maps fields from vulnerability scanner nodes (Trivy, Semgrep, AWS Inspector, etc.)
to the unified Vulnerability ontology schema.
"""

from cartography.models.ontology.mapping.specs import OntologyFieldMapping
from cartography.models.ontology.mapping.specs import OntologyMapping
from cartography.models.ontology.mapping.specs import OntologyNodeMapping

trivy_vulnerability_mapping = OntologyMapping(
    module_name="trivy",
    nodes=[
        OntologyNodeMapping(
            node_label="TrivyImageFinding",
            fields=[
                OntologyFieldMapping(
                    ontology_field="cve_id",
                    node_field="cve_id",
                    required=True,
                ),
                OntologyFieldMapping(
                    ontology_field="severity",
                    node_field="severity",
                ),
                OntologyFieldMapping(
                    ontology_field="cvss_score",
                    node_field="cvss_nvd_v3_score",
                ),
                OntologyFieldMapping(
                    ontology_field="cvss_vector",
                    node_field="cvss_nvd_v3_vector",
                ),
                OntologyFieldMapping(
                    ontology_field="description",
                    node_field="description",
                ),
                OntologyFieldMapping(
                    ontology_field="published_date",
                    node_field="published_date",
                ),
                OntologyFieldMapping(
                    ontology_field="last_modified_date",
                    node_field="last_modified_date",
                ),
            ],
        ),
    ],
)

VULNERABILITY_ONTOLOGY_MAPPING: dict[str, OntologyMapping] = {
    "trivy": trivy_vulnerability_mapping,
}
