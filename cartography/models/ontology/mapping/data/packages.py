from cartography.models.ontology.mapping.specs import OntologyFieldMapping
from cartography.models.ontology.mapping.specs import OntologyMapping
from cartography.models.ontology.mapping.specs import OntologyNodeMapping

trivy_mapping = OntologyMapping(
    module_name="trivy",
    nodes=[
        OntologyNodeMapping(
            node_label="TrivyPackage",
            fields=[
                OntologyFieldMapping(
                    ontology_field="normalized_id", node_field="normalized_id", required=True,
                ),
                OntologyFieldMapping(ontology_field="name", node_field="name"),
                OntologyFieldMapping(ontology_field="version", node_field="version"),
                OntologyFieldMapping(ontology_field="type", node_field="type"),
                OntologyFieldMapping(ontology_field="purl", node_field="purl"),
            ],
        ),
    ],
)

syft_mapping = OntologyMapping(
    module_name="syft",
    nodes=[
        OntologyNodeMapping(
            node_label="SyftPackage",
            fields=[
                OntologyFieldMapping(
                    ontology_field="normalized_id", node_field="normalized_id", required=True,
                ),
                OntologyFieldMapping(ontology_field="name", node_field="name"),
                OntologyFieldMapping(ontology_field="version", node_field="version"),
                OntologyFieldMapping(ontology_field="type", node_field="type"),
                OntologyFieldMapping(ontology_field="purl", node_field="purl"),
            ],
        ),
    ],
)

PACKAGES_ONTOLOGY_MAPPING: dict[str, OntologyMapping] = {
    "trivy": trivy_mapping,
    "syft": syft_mapping,
}
