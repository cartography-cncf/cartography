# Ontology mapping for the ComputeNamespace semantic label.
#
# _ont_name - The display name of the namespace.
# _ont_status - Current lifecycle phase of the namespace (e.g., Active, Terminating).
from cartography.models.ontology.mapping.specs import OntologyFieldMapping
from cartography.models.ontology.mapping.specs import OntologyMapping
from cartography.models.ontology.mapping.specs import OntologyNodeMapping

kubernetes_mapping = OntologyMapping(
    module_name="kubernetes",
    nodes=[
        OntologyNodeMapping(
            node_label="KubernetesNamespace",
            fields=[
                OntologyFieldMapping(ontology_field="name", node_field="name"),
                OntologyFieldMapping(
                    ontology_field="status", node_field="status_phase"
                ),
            ],
        ),
    ],
)

COMPUTENAMESPACES_ONTOLOGY_MAPPING: dict[str, OntologyMapping] = {
    "kubernetes": kubernetes_mapping,
}
