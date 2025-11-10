from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.ontology.device import DeviceSchema
from cartography.models.ontology.mapping.data.devices import DEVICES_ONTOLOGY_MAPPING
from cartography.models.ontology.mapping.data.users import USERS_ONTOLOGY_MAPPING
from cartography.models.ontology.mapping.specs import OntologyMapping
from cartography.models.ontology.user import UserSchema

ONTOLOGY_MAPPING: dict[str, dict[str, OntologyMapping]] = {
    "users": USERS_ONTOLOGY_MAPPING,
    "devices": DEVICES_ONTOLOGY_MAPPING,
}

ONTOLOGY_MODELS: dict[str, type[CartographyNodeSchema]] = {
    "users": UserSchema,
    "devices": DeviceSchema,
}
