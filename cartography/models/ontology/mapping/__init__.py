import logging

from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.ontology.device import DeviceSchema
from cartography.models.ontology.mapping.data.apikeys import APIKEYS_ONTOLOGY_MAPPING
from cartography.models.ontology.mapping.data.certificates import (
    CERTIFICATES_ONTOLOGY_MAPPING,
)
from cartography.models.ontology.mapping.data.clusters import CLUSTERS_ONTOLOGY_MAPPING
from cartography.models.ontology.mapping.data.coderepositories import (
    CODEREPOSITORIES_ONTOLOGY_MAPPING,
)
from cartography.models.ontology.mapping.data.computeinstance import (
    COMPUTE_INSTANCE_ONTOLOGY_MAPPING,
)
from cartography.models.ontology.mapping.data.computenamespaces import (
    COMPUTENAMESPACES_ONTOLOGY_MAPPING,
)
from cartography.models.ontology.mapping.data.computepods import (
    COMPUTEPODS_ONTOLOGY_MAPPING,
)
from cartography.models.ontology.mapping.data.computeservices import (
    COMPUTESERVICES_ONTOLOGY_MAPPING,
)
from cartography.models.ontology.mapping.data.containerregistries import (
    CONTAINERREGISTRIES_ONTOLOGY_MAPPING,
)
from cartography.models.ontology.mapping.data.containers import (
    CONTAINER_ONTOLOGY_MAPPING,
)
from cartography.models.ontology.mapping.data.databases import (
    DATABASES_ONTOLOGY_MAPPING,
)
from cartography.models.ontology.mapping.data.devices import DEVICES_ONTOLOGY_MAPPING
from cartography.models.ontology.mapping.data.dnsrecords import (
    DNSRECORDS_ONTOLOGY_MAPPING,
)
from cartography.models.ontology.mapping.data.dnszones import DNSZONES_ONTOLOGY_MAPPING
from cartography.models.ontology.mapping.data.encryptionkeys import (
    ENCRYPTIONKEYS_ONTOLOGY_MAPPING,
)
from cartography.models.ontology.mapping.data.file_storage import (
    FILE_STORAGE_ONTOLOGY_MAPPING,
)
from cartography.models.ontology.mapping.data.firewalls import (
    FIREWALLS_ONTOLOGY_MAPPING,
)
from cartography.models.ontology.mapping.data.functions import (
    FUNCTIONS_ONTOLOGY_MAPPING,
)
from cartography.models.ontology.mapping.data.groups import GROUPS_ONTOLOGY_MAPPING
from cartography.models.ontology.mapping.data.images import IMAGES_ONTOLOGY_MAPPING
from cartography.models.ontology.mapping.data.loadbalancers import (
    LOADBALANCERS_ONTOLOGY_MAPPING,
)
from cartography.models.ontology.mapping.data.object_storage import (
    OBJECT_STORAGE_ONTOLOGY_MAPPING,
)
from cartography.models.ontology.mapping.data.packages import PACKAGES_ONTOLOGY_MAPPING
from cartography.models.ontology.mapping.data.publicips import (
    PUBLIC_IPS_ONTOLOGY_MAPPING,
)
from cartography.models.ontology.mapping.data.roles import ROLES_ONTOLOGY_MAPPING
from cartography.models.ontology.mapping.data.secrets import SECRETS_ONTOLOGY_MAPPING
from cartography.models.ontology.mapping.data.security_issues import (
    SECURITY_ISSUES_ONTOLOGY_MAPPING,
)
from cartography.models.ontology.mapping.data.serviceaccounts import (
    SERVICEACCOUNTS_ONTOLOGY_MAPPING,
)
from cartography.models.ontology.mapping.data.tenants import TENANTS_ONTOLOGY_MAPPING
from cartography.models.ontology.mapping.data.thirdpartyapps import (
    THIRDPARTYAPPS_ONTOLOGY_MAPPING,
)
from cartography.models.ontology.mapping.data.useraccounts import (
    USERACCOUNTS_ONTOLOGY_MAPPING,
)
from cartography.models.ontology.mapping.data.users import USERS_ONTOLOGY_MAPPING
from cartography.models.ontology.mapping.specs import OntologyMapping
from cartography.models.ontology.mapping.specs import OntologyNodeMapping
from cartography.models.ontology.package import PackageSchema
from cartography.models.ontology.publicip import PublicIPSchema
from cartography.models.ontology.user import UserSchema

logger = logging.getLogger(__name__)


# Following mapping are used to create ontology nodes and relationships from module nodes
# They are leveraged in the ontology module to perform the actual mapping
ONTOLOGY_NODES_MAPPING: dict[str, dict[str, OntologyMapping]] = {
    "users": USERS_ONTOLOGY_MAPPING,
    "devices": DEVICES_ONTOLOGY_MAPPING,
    "packages": PACKAGES_ONTOLOGY_MAPPING,
    "publicips": PUBLIC_IPS_ONTOLOGY_MAPPING,
}

# Following mapping are used to normalize fields for semantic labels
# They are leveraged directly by the load functions of each module at ingestion time
SEMANTIC_LABELS_MAPPING: dict[str, dict[str, OntologyMapping]] = {
    "useraccounts": USERACCOUNTS_ONTOLOGY_MAPPING,
    "apikeys": APIKEYS_ONTOLOGY_MAPPING,
    "coderepositories": CODEREPOSITORIES_ONTOLOGY_MAPPING,
    "computeclusters": CLUSTERS_ONTOLOGY_MAPPING,
    "computeinstance": COMPUTE_INSTANCE_ONTOLOGY_MAPPING,
    "computenamespaces": COMPUTENAMESPACES_ONTOLOGY_MAPPING,
    "computepods": COMPUTEPODS_ONTOLOGY_MAPPING,
    "computeservices": COMPUTESERVICES_ONTOLOGY_MAPPING,
    "containers": CONTAINER_ONTOLOGY_MAPPING,
    "containerregistries": CONTAINERREGISTRIES_ONTOLOGY_MAPPING,
    "databases": DATABASES_ONTOLOGY_MAPPING,
    "dnsrecords": DNSRECORDS_ONTOLOGY_MAPPING,
    "dnszones": DNSZONES_ONTOLOGY_MAPPING,
    "encryptionkeys": ENCRYPTIONKEYS_ONTOLOGY_MAPPING,
    "filestorage": FILE_STORAGE_ONTOLOGY_MAPPING,
    "firewalls": FIREWALLS_ONTOLOGY_MAPPING,
    "functions": FUNCTIONS_ONTOLOGY_MAPPING,
    "groups": GROUPS_ONTOLOGY_MAPPING,
    "images": IMAGES_ONTOLOGY_MAPPING,
    "loadbalancers": LOADBALANCERS_ONTOLOGY_MAPPING,
    "objectstorage": OBJECT_STORAGE_ONTOLOGY_MAPPING,
    "roles": ROLES_ONTOLOGY_MAPPING,
    "secrets": SECRETS_ONTOLOGY_MAPPING,
    "securityissues": SECURITY_ISSUES_ONTOLOGY_MAPPING,
    "thirdpartyapps": THIRDPARTYAPPS_ONTOLOGY_MAPPING,
    "tenants": TENANTS_ONTOLOGY_MAPPING,
    "serviceaccounts": SERVICEACCOUNTS_ONTOLOGY_MAPPING,
    "certificates": CERTIFICATES_ONTOLOGY_MAPPING,
}

ONTOLOGY_MODELS: dict[str, type[CartographyNodeSchema] | None] = {
    "users": UserSchema,
    "devices": DeviceSchema,
    "packages": PackageSchema,
    "publicips": PublicIPSchema,
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
