from cartography.intel.ontology.mapping.base import OntologyMapping
from cartography.intel.ontology.mapping.devices import DEVICES_ONTOLOGY_MAPPING
from cartography.intel.ontology.mapping.users import USERS_ONTOLOGY_MAPPING

ONTOLOGY_MAPPING: dict[str, dict[str, OntologyMapping]] = {
    "users": USERS_ONTOLOGY_MAPPING,
    "devices": DEVICES_ONTOLOGY_MAPPING,
}
