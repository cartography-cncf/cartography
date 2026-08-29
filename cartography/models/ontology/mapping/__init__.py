import logging

from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabel
from cartography.models.ontology.device import DeviceSchema
from cartography.models.ontology.labels import AI_MODEL
from cartography.models.ontology.labels import API_KEY
from cartography.models.ontology.labels import BLOCK_STORAGE
from cartography.models.ontology.labels import CERTIFICATE
from cartography.models.ontology.labels import CICD_PIPELINE
from cartography.models.ontology.labels import CODE_REPOSITORY
from cartography.models.ontology.labels import COMPUTE_CLUSTER
from cartography.models.ontology.labels import COMPUTE_INSTANCE
from cartography.models.ontology.labels import COMPUTE_NAMESPACE
from cartography.models.ontology.labels import COMPUTE_POD
from cartography.models.ontology.labels import COMPUTE_SERVICE
from cartography.models.ontology.labels import CONTAINER
from cartography.models.ontology.labels import CONTAINER_REGISTRY
from cartography.models.ontology.labels import CVE
from cartography.models.ontology.labels import DATABASE
from cartography.models.ontology.labels import DNS_RECORD
from cartography.models.ontology.labels import DNS_ZONE
from cartography.models.ontology.labels import ENCRYPTION_KEY
from cartography.models.ontology.labels import FILE_STORAGE
from cartography.models.ontology.labels import FILESYSTEM_SNAPSHOT
from cartography.models.ontology.labels import FUNCTION
from cartography.models.ontology.labels import IDENTITY_PROVIDER
from cartography.models.ontology.labels import IMAGE
from cartography.models.ontology.labels import LOAD_BALANCER
from cartography.models.ontology.labels import NETWORK_ACCESS_CONTROL
from cartography.models.ontology.labels import OBJECT_STORAGE
from cartography.models.ontology.labels import PERMISSION_ROLE
from cartography.models.ontology.labels import SECRET
from cartography.models.ontology.labels import SECURITY_ISSUE
from cartography.models.ontology.labels import SERVICE_ACCOUNT
from cartography.models.ontology.labels import SNAPSHOT
from cartography.models.ontology.labels import SUBNET
from cartography.models.ontology.labels import TAG
from cartography.models.ontology.labels import TENANT
from cartography.models.ontology.labels import THIRD_PARTY_APP
from cartography.models.ontology.labels import USER_ACCOUNT
from cartography.models.ontology.labels import USER_GROUP
from cartography.models.ontology.labels import VIRTUAL_NETWORK
from cartography.models.ontology.mapping.data.aimodels import AIMODELS_ONTOLOGY_MAPPING
from cartography.models.ontology.mapping.data.apikeys import APIKEYS_ONTOLOGY_MAPPING
from cartography.models.ontology.mapping.data.blockstorage import (
    BLOCK_STORAGE_ONTOLOGY_MAPPING,
)
from cartography.models.ontology.mapping.data.certificates import (
    CERTIFICATES_ONTOLOGY_MAPPING,
)
from cartography.models.ontology.mapping.data.cicdpipelines import (
    CICDPIPELINES_ONTOLOGY_MAPPING,
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
from cartography.models.ontology.mapping.data.cves import CVES_ONTOLOGY_MAPPING
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
from cartography.models.ontology.mapping.data.filesystem_snapshots import (
    FILESYSTEM_SNAPSHOTS_ONTOLOGY_MAPPING,
)
from cartography.models.ontology.mapping.data.firewalls import (
    FIREWALLS_ONTOLOGY_MAPPING,
)
from cartography.models.ontology.mapping.data.functions import (
    FUNCTIONS_ONTOLOGY_MAPPING,
)
from cartography.models.ontology.mapping.data.groups import GROUPS_ONTOLOGY_MAPPING
from cartography.models.ontology.mapping.data.identityproviders import (
    IDENTITYPROVIDERS_ONTOLOGY_MAPPING,
)
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
from cartography.models.ontology.mapping.data.snapshots import (
    SNAPSHOTS_ONTOLOGY_MAPPING,
)
from cartography.models.ontology.mapping.data.subnets import SUBNETS_ONTOLOGY_MAPPING
from cartography.models.ontology.mapping.data.tags import TAGS_ONTOLOGY_MAPPING
from cartography.models.ontology.mapping.data.tenants import TENANTS_ONTOLOGY_MAPPING
from cartography.models.ontology.mapping.data.thirdpartyapps import (
    THIRDPARTYAPPS_ONTOLOGY_MAPPING,
)
from cartography.models.ontology.mapping.data.useraccounts import (
    USERACCOUNTS_ONTOLOGY_MAPPING,
)
from cartography.models.ontology.mapping.data.users import USERS_ONTOLOGY_MAPPING
from cartography.models.ontology.mapping.data.vpcs import VPCS_ONTOLOGY_MAPPING
from cartography.models.ontology.mapping.specs import OntologyMapping
from cartography.models.ontology.mapping.specs import OntologyNodeMapping
from cartography.models.ontology.package import PackageSchema
from cartography.models.ontology.package_version import PackageVersionSchema
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
    "aimodels": AIMODELS_ONTOLOGY_MAPPING,
    "apikeys": APIKEYS_ONTOLOGY_MAPPING,
    "blockstorage": BLOCK_STORAGE_ONTOLOGY_MAPPING,
    "cicdpipelines": CICDPIPELINES_ONTOLOGY_MAPPING,
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
    "filesystemsnapshots": FILESYSTEM_SNAPSHOTS_ONTOLOGY_MAPPING,
    "firewalls": FIREWALLS_ONTOLOGY_MAPPING,
    "functions": FUNCTIONS_ONTOLOGY_MAPPING,
    "groups": GROUPS_ONTOLOGY_MAPPING,
    "identityproviders": IDENTITYPROVIDERS_ONTOLOGY_MAPPING,
    "images": IMAGES_ONTOLOGY_MAPPING,
    "loadbalancers": LOADBALANCERS_ONTOLOGY_MAPPING,
    "objectstorage": OBJECT_STORAGE_ONTOLOGY_MAPPING,
    "roles": ROLES_ONTOLOGY_MAPPING,
    "secrets": SECRETS_ONTOLOGY_MAPPING,
    "securityissues": SECURITY_ISSUES_ONTOLOGY_MAPPING,
    "snapshots": SNAPSHOTS_ONTOLOGY_MAPPING,
    "subnets": SUBNETS_ONTOLOGY_MAPPING,
    "tags": TAGS_ONTOLOGY_MAPPING,
    "vpcs": VPCS_ONTOLOGY_MAPPING,
    "thirdpartyapps": THIRDPARTYAPPS_ONTOLOGY_MAPPING,
    "tenants": TENANTS_ONTOLOGY_MAPPING,
    "serviceaccounts": SERVICEACCOUNTS_ONTOLOGY_MAPPING,
    "certificates": CERTIFICATES_ONTOLOGY_MAPPING,
    "cves": CVES_ONTOLOGY_MAPPING,
}

# The ontology extra label carried by every node mapped in a given semantic category.
# Provider schemas mapped into a category must declare that label (enforced by
# tests/unit/cartography/intel/ontology/test_ontology_mapping.py), otherwise their nodes get
# normalized `_ont_*` properties while staying invisible to `MATCH (n:<Label>)` queries.
SEMANTIC_LABEL_BY_CATEGORY: dict[str, ExtraNodeLabel] = {
    "aimodels": AI_MODEL,
    "apikeys": API_KEY,
    "blockstorage": BLOCK_STORAGE,
    "certificates": CERTIFICATE,
    "cicdpipelines": CICD_PIPELINE,
    "coderepositories": CODE_REPOSITORY,
    "computeclusters": COMPUTE_CLUSTER,
    "computeinstance": COMPUTE_INSTANCE,
    "computenamespaces": COMPUTE_NAMESPACE,
    "computepods": COMPUTE_POD,
    "computeservices": COMPUTE_SERVICE,
    "containerregistries": CONTAINER_REGISTRY,
    "containers": CONTAINER,
    "cves": CVE,
    "databases": DATABASE,
    "dnsrecords": DNS_RECORD,
    "dnszones": DNS_ZONE,
    "encryptionkeys": ENCRYPTION_KEY,
    "filestorage": FILE_STORAGE,
    "filesystemsnapshots": FILESYSTEM_SNAPSHOT,
    "firewalls": NETWORK_ACCESS_CONTROL,
    "functions": FUNCTION,
    "groups": USER_GROUP,
    "identityproviders": IDENTITY_PROVIDER,
    "images": IMAGE,
    "loadbalancers": LOAD_BALANCER,
    "objectstorage": OBJECT_STORAGE,
    "roles": PERMISSION_ROLE,
    "secrets": SECRET,
    "securityissues": SECURITY_ISSUE,
    "serviceaccounts": SERVICE_ACCOUNT,
    "snapshots": SNAPSHOT,
    "subnets": SUBNET,
    "tags": TAG,
    "tenants": TENANT,
    "thirdpartyapps": THIRD_PARTY_APP,
    "useraccounts": USER_ACCOUNT,
    "vpcs": VIRTUAL_NETWORK,
}


SEMANTIC_LABELS_WITHOUT_NORMALIZED_FIELDS: tuple[str, ...] = (
    "ImageAttestation",
    "ImageLayer",
    "ImageManifestList",
    "ImageTag",
)

ONTOLOGY_MODELS: dict[str, type[CartographyNodeSchema] | None] = {
    "users": UserSchema,
    "devices": DeviceSchema,
    "packages": PackageVersionSchema,
    "publicips": PublicIPSchema,
}

# Primary labels owned by canonical ontology schemas. Provider schemas must never
# reuse them (enforced by tests/unit/cartography/intel/ontology/test_ontology_mapping.py).
# This is a superset of ONTOLOGY_MODELS: Package is not built from an ontology mapping,
# it is derived from the PackageVersion rows by the ontology packages sync.
ONTOLOGY_CANONICAL_SCHEMAS: tuple[type[CartographyNodeSchema], ...] = (
    UserSchema,
    DeviceSchema,
    PackageSchema,
    PackageVersionSchema,
    PublicIPSchema,
)


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


def get_deprecated_ontology_index_properties() -> set[str]:
    """DEPRECATED: temporary backward-compatibility helper. Remove in v1.0.0.

    Returns the set of `_ont_<field>` property names whose RANGE index was removed by the
    `indexed=False` opt-out (#2845). Graphs synced before that change still carry these indexes
    on their semantic labels; this set is used to drop them. Driven entirely by the data model:
    any field flagged `indexed=False` is picked up automatically.
    """
    props: set[str] = set()
    for module_mappings in (
        *SEMANTIC_LABELS_MAPPING.values(),
        *ONTOLOGY_NODES_MAPPING.values(),
    ):
        for ontology_mapping in module_mappings.values():
            for node in ontology_mapping.nodes:
                for mapping_field in node.fields:
                    if not mapping_field.indexed:
                        props.add(f"_ont_{mapping_field.ontology_field}")
    return props
