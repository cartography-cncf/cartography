from dataclasses import dataclass

from cartography.models.core.nodes import ExtraNodeLabel


@dataclass(frozen=True)
class AIModelOntologyLabel(ExtraNodeLabel):
    """A cross-provider AIModel resource in Cartography's ontology."""

    label: str = "AIModel"
    ontology: bool = True


@dataclass(frozen=True)
class APIKeyOntologyLabel(ExtraNodeLabel):
    """A cross-provider APIKey resource in Cartography's ontology."""

    label: str = "APIKey"
    ontology: bool = True


@dataclass(frozen=True)
class BlockStorageOntologyLabel(ExtraNodeLabel):
    """A cross-provider BlockStorage resource in Cartography's ontology."""

    label: str = "BlockStorage"
    ontology: bool = True


@dataclass(frozen=True)
class CICDPipelineOntologyLabel(ExtraNodeLabel):
    """A cross-provider CICDPipeline resource in Cartography's ontology."""

    label: str = "CICDPipeline"
    ontology: bool = True


@dataclass(frozen=True)
class CVEOntologyLabel(ExtraNodeLabel):
    """A cross-provider CVE resource in Cartography's ontology."""

    label: str = "CVE"
    ontology: bool = True


@dataclass(frozen=True)
class CertificateOntologyLabel(ExtraNodeLabel):
    """A cross-provider Certificate resource in Cartography's ontology."""

    label: str = "Certificate"
    ontology: bool = True


@dataclass(frozen=True)
class CodeRepositoryOntologyLabel(ExtraNodeLabel):
    """A cross-provider CodeRepository resource in Cartography's ontology."""

    label: str = "CodeRepository"
    ontology: bool = True


@dataclass(frozen=True)
class ComputeClusterOntologyLabel(ExtraNodeLabel):
    """A cross-provider ComputeCluster resource in Cartography's ontology."""

    label: str = "ComputeCluster"
    ontology: bool = True


@dataclass(frozen=True)
class ComputeInstanceOntologyLabel(ExtraNodeLabel):
    """A cross-provider ComputeInstance resource in Cartography's ontology."""

    label: str = "ComputeInstance"
    ontology: bool = True


@dataclass(frozen=True)
class ComputeNamespaceOntologyLabel(ExtraNodeLabel):
    """A cross-provider ComputeNamespace resource in Cartography's ontology."""

    label: str = "ComputeNamespace"
    ontology: bool = True


@dataclass(frozen=True)
class ComputePodOntologyLabel(ExtraNodeLabel):
    """A cross-provider ComputePod resource in Cartography's ontology."""

    label: str = "ComputePod"
    ontology: bool = True


@dataclass(frozen=True)
class ComputeServiceOntologyLabel(ExtraNodeLabel):
    """A cross-provider ComputeService resource in Cartography's ontology."""

    label: str = "ComputeService"
    ontology: bool = True


@dataclass(frozen=True)
class ContainerOntologyLabel(ExtraNodeLabel):
    """A cross-provider Container resource in Cartography's ontology."""

    label: str = "Container"
    ontology: bool = True


@dataclass(frozen=True)
class ContainerRegistryOntologyLabel(ExtraNodeLabel):
    """A cross-provider ContainerRegistry resource in Cartography's ontology."""

    label: str = "ContainerRegistry"
    ontology: bool = True


@dataclass(frozen=True)
class DNSRecordOntologyLabel(ExtraNodeLabel):
    """A cross-provider DNSRecord resource in Cartography's ontology."""

    label: str = "DNSRecord"
    ontology: bool = True


@dataclass(frozen=True)
class DNSZoneOntologyLabel(ExtraNodeLabel):
    """A cross-provider DNSZone resource in Cartography's ontology."""

    label: str = "DNSZone"
    ontology: bool = True


@dataclass(frozen=True)
class DatabaseOntologyLabel(ExtraNodeLabel):
    """A cross-provider Database resource in Cartography's ontology."""

    label: str = "Database"
    ontology: bool = True


@dataclass(frozen=True)
class EncryptionKeyOntologyLabel(ExtraNodeLabel):
    """A cross-provider EncryptionKey resource in Cartography's ontology."""

    label: str = "EncryptionKey"
    ontology: bool = True


@dataclass(frozen=True)
class FileStorageOntologyLabel(ExtraNodeLabel):
    """A cross-provider FileStorage resource in Cartography's ontology."""

    label: str = "FileStorage"
    ontology: bool = True


@dataclass(frozen=True)
class FunctionOntologyLabel(ExtraNodeLabel):
    """A cross-provider Function resource in Cartography's ontology."""

    label: str = "Function"
    ontology: bool = True


@dataclass(frozen=True)
class IdentityProviderOntologyLabel(ExtraNodeLabel):
    """A cross-provider IdentityProvider resource in Cartography's ontology."""

    label: str = "IdentityProvider"
    ontology: bool = True


@dataclass(frozen=True)
class ImageOntologyLabel(ExtraNodeLabel):
    """A concrete single-platform container image."""

    label: str = "Image"
    ontology: bool = True


@dataclass(frozen=True)
class ImageAttestationOntologyLabel(ExtraNodeLabel):
    """A cross-provider ImageAttestation resource in Cartography's ontology."""

    label: str = "ImageAttestation"
    ontology: bool = True


@dataclass(frozen=True)
class ImageLayerOntologyLabel(ExtraNodeLabel):
    """A cross-provider ImageLayer resource in Cartography's ontology."""

    label: str = "ImageLayer"
    ontology: bool = True


@dataclass(frozen=True)
class ImageManifestListOntologyLabel(ExtraNodeLabel):
    """A cross-provider ImageManifestList resource in Cartography's ontology."""

    label: str = "ImageManifestList"
    ontology: bool = True


@dataclass(frozen=True)
class ImageTagOntologyLabel(ExtraNodeLabel):
    """A cross-provider ImageTag resource in Cartography's ontology."""

    label: str = "ImageTag"
    ontology: bool = True


@dataclass(frozen=True)
class LoadBalancerOntologyLabel(ExtraNodeLabel):
    """A cross-provider LoadBalancer resource in Cartography's ontology."""

    label: str = "LoadBalancer"
    ontology: bool = True


@dataclass(frozen=True)
class NetworkAccessControlOntologyLabel(ExtraNodeLabel):
    """A cross-provider NetworkAccessControl resource in Cartography's ontology."""

    label: str = "NetworkAccessControl"
    ontology: bool = True


@dataclass(frozen=True)
class ObjectStorageOntologyLabel(ExtraNodeLabel):
    """A cross-provider ObjectStorage resource in Cartography's ontology."""

    label: str = "ObjectStorage"
    ontology: bool = True


@dataclass(frozen=True)
class CanonicalOntologyLabel(ExtraNodeLabel):
    """A canonical node managed by Cartography's cross-provider ontology."""

    label: str = "Ontology"
    ontology: bool = True


@dataclass(frozen=True)
class PermissionRoleOntologyLabel(ExtraNodeLabel):
    """A cross-provider PermissionRole resource in Cartography's ontology."""

    label: str = "PermissionRole"
    ontology: bool = True


@dataclass(frozen=True)
class SecretOntologyLabel(ExtraNodeLabel):
    """A cross-provider Secret resource in Cartography's ontology."""

    label: str = "Secret"
    ontology: bool = True


@dataclass(frozen=True)
class SecurityIssueOntologyLabel(ExtraNodeLabel):
    """A cross-provider SecurityIssue resource in Cartography's ontology."""

    label: str = "SecurityIssue"
    ontology: bool = True


@dataclass(frozen=True)
class ServiceAccountOntologyLabel(ExtraNodeLabel):
    """A cross-provider ServiceAccount resource in Cartography's ontology."""

    label: str = "ServiceAccount"
    ontology: bool = True


@dataclass(frozen=True)
class SnapshotOntologyLabel(ExtraNodeLabel):
    """A cross-provider Snapshot resource in Cartography's ontology."""

    label: str = "Snapshot"
    ontology: bool = True


@dataclass(frozen=True)
class SubnetOntologyLabel(ExtraNodeLabel):
    """A cross-provider Subnet resource in Cartography's ontology."""

    label: str = "Subnet"
    ontology: bool = True


@dataclass(frozen=True)
class TagOntologyLabel(ExtraNodeLabel):
    """A cross-provider Tag resource in Cartography's ontology."""

    label: str = "Tag"
    ontology: bool = True


@dataclass(frozen=True)
class TenantOntologyLabel(ExtraNodeLabel):
    """A cross-provider Tenant resource in Cartography's ontology."""

    label: str = "Tenant"
    ontology: bool = True


@dataclass(frozen=True)
class ThirdPartyAppOntologyLabel(ExtraNodeLabel):
    """A cross-provider ThirdPartyApp resource in Cartography's ontology."""

    label: str = "ThirdPartyApp"
    ontology: bool = True


@dataclass(frozen=True)
class UserAccountOntologyLabel(ExtraNodeLabel):
    """An identity on a specific system or service."""

    label: str = "UserAccount"
    ontology: bool = True


@dataclass(frozen=True)
class UserGroupOntologyLabel(ExtraNodeLabel):
    """A cross-provider UserGroup resource in Cartography's ontology."""

    label: str = "UserGroup"
    ontology: bool = True


@dataclass(frozen=True)
class VirtualNetworkOntologyLabel(ExtraNodeLabel):
    """A cross-provider VirtualNetwork resource in Cartography's ontology."""

    label: str = "VirtualNetwork"
    ontology: bool = True
