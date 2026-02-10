"""Ontology field mappings for software package data.

Maps fields from package source nodes (Trivy, SBOM files, package managers, etc.)
to the unified SoftwarePackage ontology schema.
"""

from cartography.models.ontology.mapping.specs import OntologyFieldMapping
from cartography.models.ontology.mapping.specs import OntologyMapping
from cartography.models.ontology.mapping.specs import OntologyNodeMapping

trivy_package_mapping = OntologyMapping(
    module_name="trivy",
    nodes=[
        OntologyNodeMapping(
            node_label="Package",
            fields=[
                OntologyFieldMapping(
                    ontology_field="id",
                    node_field="id",
                    required=True,
                ),
                OntologyFieldMapping(
                    ontology_field="name",
                    node_field="name",
                ),
                OntologyFieldMapping(
                    ontology_field="version",
                    node_field="version",
                ),
                OntologyFieldMapping(
                    ontology_field="type",
                    node_field="type",
                ),
                OntologyFieldMapping(
                    ontology_field="purl",
                    node_field="purl",
                ),
            ],
        ),
    ],
)

PACKAGE_ONTOLOGY_MAPPING: dict[str, OntologyMapping] = {
    "trivy": trivy_package_mapping,
}
