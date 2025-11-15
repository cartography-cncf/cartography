import logging

from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.ontology.device import DeviceSchema
from cartography.models.ontology.mapping.data.devices import DEVICES_ONTOLOGY_MAPPING
from cartography.models.ontology.mapping.data.useraccounts import (
    USERACCOUNTS_ONTOLOGY_MAPPING,
)
from cartography.models.ontology.mapping.data.users import USERS_ONTOLOGY_MAPPING
from cartography.models.ontology.mapping.specs import OntologyMapping
from cartography.models.ontology.mapping.specs import OntologyNodeMapping
from cartography.models.ontology.user import UserSchema

logger = logging.getLogger(__name__)

ONTOLOGY_MAPPING: dict[str, dict[str, OntologyMapping]] = {
    "users": USERS_ONTOLOGY_MAPPING,
    "devices": DEVICES_ONTOLOGY_MAPPING,
    "useraccounts": USERACCOUNTS_ONTOLOGY_MAPPING,
}

ONTOLOGY_MODELS: dict[str, type[CartographyNodeSchema] | None] = {
    "users": UserSchema,
    "devices": DeviceSchema,
    # Following labels are only semantic labels no independent nodes exist
    # So there is no corresponding model class
    "useraccounts": None,
}


def get_mapping_from_node_schema(
    node_schema: CartographyNodeSchema,
) -> OntologyNodeMapping | None:
    """Retrieve the OntologyNodeMapping for a given CartographyNodeSchema.

    Args:
        node_schema: An instance of CartographyNodeSchema representing the node.

    Returns:
        The corresponding OntologyNodeMapping if found, else None.
    """
    for module_name, module_mappings in ONTOLOGY_MAPPING.items():
        if module_name == "ontology":
            continue
        for ontology_mapping in module_mappings.values():
            for mapping_node in ontology_mapping.nodes:
                if mapping_node.node_label == node_schema.label:
                    logging.debug(
                        "Found mapping for node label: %s", mapping_node.node_label
                    )
                    return mapping_node
    return None
