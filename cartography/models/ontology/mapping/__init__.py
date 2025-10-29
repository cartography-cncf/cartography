from cartography.models.ontology.mapping.data.devices import DEVICES_ONTOLOGY_MAPPING
from cartography.models.ontology.mapping.data.users import USERS_ONTOLOGY_MAPPING
from cartography.models.ontology.mapping.specs import OntologyMapping

ONTOLOGY_MAPPING: dict[str, dict[str, OntologyMapping]] = {
    "users": USERS_ONTOLOGY_MAPPING,
    "devices": DEVICES_ONTOLOGY_MAPPING,
}
