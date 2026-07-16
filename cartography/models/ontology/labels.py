from cartography.models.core.nodes import ExtraNodeLabel
from cartography.models.core.nodes import LabelKind

AI_MODEL = ExtraNodeLabel(
    label="AIModel",
    description="A cross-provider AIModel resource in Cartography's ontology.",
    kind=LabelKind.ONTOLOGY,
)


API_KEY = ExtraNodeLabel(
    label="APIKey",
    description="A cross-provider APIKey resource in Cartography's ontology.",
    kind=LabelKind.ONTOLOGY,
)


BLOCK_STORAGE = ExtraNodeLabel(
    label="BlockStorage",
    description="A cross-provider BlockStorage resource in Cartography's ontology.",
    kind=LabelKind.ONTOLOGY,
)


CICD_PIPELINE = ExtraNodeLabel(
    label="CICDPipeline",
    description="A cross-provider CICDPipeline resource in Cartography's ontology.",
    kind=LabelKind.ONTOLOGY,
)


CVE = ExtraNodeLabel(
    label="CVE",
    description="A cross-provider CVE resource in Cartography's ontology.",
    kind=LabelKind.ONTOLOGY,
)


CERTIFICATE = ExtraNodeLabel(
    label="Certificate",
    description="A cross-provider Certificate resource in Cartography's ontology.",
    kind=LabelKind.ONTOLOGY,
)


CODE_REPOSITORY = ExtraNodeLabel(
    label="CodeRepository",
    description="A cross-provider CodeRepository resource in Cartography's ontology.",
    kind=LabelKind.ONTOLOGY,
)


COMPUTE_CLUSTER = ExtraNodeLabel(
    label="ComputeCluster",
    description="A cross-provider ComputeCluster resource in Cartography's ontology.",
    kind=LabelKind.ONTOLOGY,
)


COMPUTE_INSTANCE = ExtraNodeLabel(
    label="ComputeInstance",
    description="A cross-provider ComputeInstance resource in Cartography's ontology.",
    kind=LabelKind.ONTOLOGY,
)


COMPUTE_NAMESPACE = ExtraNodeLabel(
    label="ComputeNamespace",
    description="A cross-provider ComputeNamespace resource in Cartography's ontology.",
    kind=LabelKind.ONTOLOGY,
)


COMPUTE_POD = ExtraNodeLabel(
    label="ComputePod",
    description="A cross-provider ComputePod resource in Cartography's ontology.",
    kind=LabelKind.ONTOLOGY,
)


COMPUTE_SERVICE = ExtraNodeLabel(
    label="ComputeService",
    description="A cross-provider ComputeService resource in Cartography's ontology.",
    kind=LabelKind.ONTOLOGY,
)


CONTAINER = ExtraNodeLabel(
    label="Container",
    description="A cross-provider Container resource in Cartography's ontology.",
    kind=LabelKind.ONTOLOGY,
)


CONTAINER_REGISTRY = ExtraNodeLabel(
    label="ContainerRegistry",
    description="A cross-provider ContainerRegistry resource in Cartography's ontology.",
    kind=LabelKind.ONTOLOGY,
)


DNS_RECORD = ExtraNodeLabel(
    label="DNSRecord",
    description="A cross-provider DNSRecord resource in Cartography's ontology.",
    kind=LabelKind.ONTOLOGY,
)


DNS_ZONE = ExtraNodeLabel(
    label="DNSZone",
    description="A cross-provider DNSZone resource in Cartography's ontology.",
    kind=LabelKind.ONTOLOGY,
)


DATABASE = ExtraNodeLabel(
    label="Database",
    description="A cross-provider Database resource in Cartography's ontology.",
    kind=LabelKind.ONTOLOGY,
)


ENCRYPTION_KEY = ExtraNodeLabel(
    label="EncryptionKey",
    description="A cross-provider EncryptionKey resource in Cartography's ontology.",
    kind=LabelKind.ONTOLOGY,
)


FILE_STORAGE = ExtraNodeLabel(
    label="FileStorage",
    description="A cross-provider FileStorage resource in Cartography's ontology.",
    kind=LabelKind.ONTOLOGY,
)


FUNCTION = ExtraNodeLabel(
    label="Function",
    description="A cross-provider Function resource in Cartography's ontology.",
    kind=LabelKind.ONTOLOGY,
)


IDENTITY_PROVIDER = ExtraNodeLabel(
    label="IdentityProvider",
    description="A cross-provider IdentityProvider resource in Cartography's ontology.",
    kind=LabelKind.ONTOLOGY,
)


IMAGE = ExtraNodeLabel(
    label="Image",
    description="A concrete single-platform container image.",
    kind=LabelKind.ONTOLOGY,
)


IMAGE_ATTESTATION = ExtraNodeLabel(
    label="ImageAttestation",
    description="A cross-provider ImageAttestation resource in Cartography's ontology.",
    kind=LabelKind.ONTOLOGY,
)


IMAGE_LAYER = ExtraNodeLabel(
    label="ImageLayer",
    description="A cross-provider ImageLayer resource in Cartography's ontology.",
    kind=LabelKind.ONTOLOGY,
)


IMAGE_MANIFEST_LIST = ExtraNodeLabel(
    label="ImageManifestList",
    description="A cross-provider ImageManifestList resource in Cartography's ontology.",
    kind=LabelKind.ONTOLOGY,
)


IMAGE_TAG = ExtraNodeLabel(
    label="ImageTag",
    description="A cross-provider ImageTag resource in Cartography's ontology.",
    kind=LabelKind.ONTOLOGY,
)


LOAD_BALANCER = ExtraNodeLabel(
    label="LoadBalancer",
    description="A cross-provider LoadBalancer resource in Cartography's ontology.",
    kind=LabelKind.ONTOLOGY,
)


NETWORK_ACCESS_CONTROL = ExtraNodeLabel(
    label="NetworkAccessControl",
    description="A cross-provider NetworkAccessControl resource in Cartography's ontology.",
    kind=LabelKind.ONTOLOGY,
)


OBJECT_STORAGE = ExtraNodeLabel(
    label="ObjectStorage",
    description="A cross-provider ObjectStorage resource in Cartography's ontology.",
    kind=LabelKind.ONTOLOGY,
)


ONTOLOGY = ExtraNodeLabel(
    label="Ontology",
    description="A canonical node managed by Cartography's cross-provider ontology.",
    kind=LabelKind.ONTOLOGY,
)


PERMISSION_ROLE = ExtraNodeLabel(
    label="PermissionRole",
    description="A cross-provider PermissionRole resource in Cartography's ontology.",
    kind=LabelKind.ONTOLOGY,
)


SECRET = ExtraNodeLabel(
    label="Secret",
    description="A cross-provider Secret resource in Cartography's ontology.",
    kind=LabelKind.ONTOLOGY,
)


SECURITY_ISSUE = ExtraNodeLabel(
    label="SecurityIssue",
    description="A cross-provider SecurityIssue resource in Cartography's ontology.",
    kind=LabelKind.ONTOLOGY,
)


SERVICE_ACCOUNT = ExtraNodeLabel(
    label="ServiceAccount",
    description="A cross-provider ServiceAccount resource in Cartography's ontology.",
    kind=LabelKind.ONTOLOGY,
)


SNAPSHOT = ExtraNodeLabel(
    label="Snapshot",
    description="A cross-provider Snapshot resource in Cartography's ontology.",
    kind=LabelKind.ONTOLOGY,
)


SUBNET = ExtraNodeLabel(
    label="Subnet",
    description="A cross-provider Subnet resource in Cartography's ontology.",
    kind=LabelKind.ONTOLOGY,
)


TAG = ExtraNodeLabel(
    label="Tag",
    description="A cross-provider Tag resource in Cartography's ontology.",
    kind=LabelKind.ONTOLOGY,
)


TENANT = ExtraNodeLabel(
    label="Tenant",
    description="A cross-provider Tenant resource in Cartography's ontology.",
    kind=LabelKind.ONTOLOGY,
)


THIRD_PARTY_APP = ExtraNodeLabel(
    label="ThirdPartyApp",
    description="A cross-provider ThirdPartyApp resource in Cartography's ontology.",
    kind=LabelKind.ONTOLOGY,
)


USER_ACCOUNT = ExtraNodeLabel(
    label="UserAccount",
    description="An identity on a specific system or service.",
    kind=LabelKind.ONTOLOGY,
)


USER_GROUP = ExtraNodeLabel(
    label="UserGroup",
    description="A cross-provider UserGroup resource in Cartography's ontology.",
    kind=LabelKind.ONTOLOGY,
)


VIRTUAL_NETWORK = ExtraNodeLabel(
    label="VirtualNetwork",
    description="A cross-provider VirtualNetwork resource in Cartography's ontology.",
    kind=LabelKind.ONTOLOGY,
)
