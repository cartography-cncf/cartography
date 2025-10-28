from cartography.intel.ontology.mapping.base import OntologyMapping
from cartography.intel.ontology.mapping.devices import DEVICES_ONTOLOGY_MAPPING
from cartography.intel.ontology.mapping.users import USERS_ONTOLOGY_MAPPING

ONTOLOGY_MAPPING: dict[str, dict[str, OntologyMapping]] = {
    "users": USERS_ONTOLOGY_MAPPING,
    "devices": DEVICES_ONTOLOGY_MAPPING,
}


# WIP: Remove from data (delete file + pyproject + loading)
# WIP: add test to check that key in mappings are real modules
# WIP: check consistency between dict key and module_name in OntologyMapping
# WIP: add test to check that mapping values are field and field are extra indexed
