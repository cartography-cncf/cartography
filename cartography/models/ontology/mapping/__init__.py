import logging

from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.ontology.device import DeviceSchema
from cartography.models.ontology.mapping.data.apikeys import APIKEYS_ONTOLOGY_MAPPING
from cartography.models.ontology.mapping.data.computeinstance import (
    COMPUTE_INSTANCE_ONTOLOGY_MAPPING,
)
from cartography.models.ontology.mapping.data.containers import (
    CONTAINER_ONTOLOGY_MAPPING,
)
from cartography.models.ontology.mapping.data.databases import (
    DATABASES_ONTOLOGY_MAPPING,
)
from cartography.models.ontology.mapping.data.devices import DEVICES_ONTOLOGY_MAPPING
from cartography.models.ontology.mapping.data.thirdpartyapps import (
    THIRDPARTYAPPS_ONTOLOGY_MAPPING,
)
from cartography.models.ontology.mapping.data.useraccounts import (
    USERACCOUNTS_ONTOLOGY_MAPPING,
)
from cartography.models.ontology.mapping.data.users import USERS_ONTOLOGY_MAPPING
from cartography.models.ontology.mapping.specs import OntologyMapping
from cartography.models.ontology.mapping.specs import OntologyNodeMapping
from cartography.models.ontology.user import UserSchema

logger = logging.getLogger(__name__)


# Following mapping are used to create ontology nodes and relationships from module nodes
# They are leveraged in the ontology module to perform the actual mapping
ONTOLOGY_NODES_MAPPING: dict[str, dict[str, OntologyMapping]] = {
    "users": USERS_ONTOLOGY_MAPPING,
    "devices": DEVICES_ONTOLOGY_MAPPING,
}

# Following mapping are used to normalize fields for semantic labels
# They are leveraged directly by the load functions of each module at ingestion time
SEMANTIC_LABELS_MAPPING: dict[str, dict[str, OntologyMapping]] = {
    "useraccounts": USERACCOUNTS_ONTOLOGY_MAPPING,
    "apikeys": APIKEYS_ONTOLOGY_MAPPING,
    "computeinstance": COMPUTE_INSTANCE_ONTOLOGY_MAPPING,
    "containers": CONTAINER_ONTOLOGY_MAPPING,
    "databases": DATABASES_ONTOLOGY_MAPPING,
    "thirdpartyapps": THIRDPARTYAPPS_ONTOLOGY_MAPPING,
}

ONTOLOGY_MODELS: dict[str, type[CartographyNodeSchema] | None] = {
    "users": UserSchema,
    "devices": DeviceSchema,
}


def get_semantic_label_mapping_from_node_schema(
    node_schema: CartographyNodeSchema,
) -> OntologyNodeMapping | None:
    """Retrieve the OntologyNodeMapping for a given CartographyNodeSchema.

    Args:
        node_schema: An instance of CartographyNodeSchema representing the node.

    Returns:
        The corresponding OntologyNodeMapping if found, else None.
    """
    for module_name, module_mappings in SEMANTIC_LABELS_MAPPING.items():
        if module_name == "ontology":
            continue
        for ontology_mapping in module_mappings.values():
            for mapping_node in ontology_mapping.nodes:
                if mapping_node.node_label == node_schema.label:
                    logging.debug(
                        "Found semantic label mapping for node label: %s",
                        mapping_node.node_label,
                    )
                    return mapping_node
    return None
