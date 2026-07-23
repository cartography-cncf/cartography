# Ontology mapping for the ComputeNamespace semantic label.
#
# _ont_name - The display name of the namespace.
# _ont_status - Namespace lifecycle, normalized to the shared canonical set:
#   active, creating, terminating, deleting, error, unknown.
#   The raw provider value stays on the source node's own status property.
from cartography.models.ontology.mapping.specs import OntologyFieldMapping
from cartography.models.ontology.mapping.specs import OntologyMapping
from cartography.models.ontology.mapping.specs import OntologyNodeMapping

# Kubernetes NamespacePhase
_K8S_NAMESPACE_STATUS = {
    "Active": "active",
    "Terminating": "terminating",
}

# Scaleway function/container NamespaceStatus
_SCALEWAY_NAMESPACE_STATUS = {
    "unknown": "unknown",
    "creating": "creating",
    "pending": "creating",
    "ready": "active",
    "deleting": "deleting",
    "error": "error",
    "locked": "error",
}

kubernetes_mapping = OntologyMapping(
    module_name="kubernetes",
    nodes=[
        OntologyNodeMapping(
            node_label="KubernetesNamespace",
            fields=[
                OntologyFieldMapping(ontology_field="name", node_field="name"),
                OntologyFieldMapping(
                    ontology_field="status",
                    node_field="status_phase",
                    special_handling="mapping",
                    extra={"map": _K8S_NAMESPACE_STATUS},
                ),
            ],
        ),
    ],
)

scaleway_mapping = OntologyMapping(
    module_name="scaleway",
    nodes=[
        OntologyNodeMapping(
            node_label="ScalewayServerlessFunctionNamespace",
            fields=[
                OntologyFieldMapping(ontology_field="name", node_field="name"),
                OntologyFieldMapping(
                    ontology_field="status",
                    node_field="status",
                    special_handling="mapping",
                    extra={"map": _SCALEWAY_NAMESPACE_STATUS},
                ),
            ],
        ),
        OntologyNodeMapping(
            node_label="ScalewayServerlessContainerNamespace",
            fields=[
                OntologyFieldMapping(ontology_field="name", node_field="name"),
                OntologyFieldMapping(
                    ontology_field="status",
                    node_field="status",
                    special_handling="mapping",
                    extra={"map": _SCALEWAY_NAMESPACE_STATUS},
                ),
            ],
        ),
    ],
)

COMPUTENAMESPACES_ONTOLOGY_MAPPING: dict[str, OntologyMapping] = {
    "kubernetes": kubernetes_mapping,
    "scaleway": scaleway_mapping,
}
