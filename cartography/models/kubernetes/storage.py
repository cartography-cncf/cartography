from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class KubernetesStorageClassNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Identifier derived from cluster name and StorageClass name.",
    )
    uid: PropertyRef = PropertyRef(
        "uid", description="Kubernetes UID of the StorageClass."
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Name of the StorageClass."
    )
    creation_timestamp: PropertyRef = PropertyRef(
        "creation_timestamp",
        description="Timestamp when the StorageClass was created.",
    )
    deletion_timestamp: PropertyRef = PropertyRef(
        "deletion_timestamp",
        description="Timestamp when the StorageClass was marked for deletion.",
    )
    cluster_name: PropertyRef = PropertyRef(
        "CLUSTER_NAME",
        set_in_kwargs=True,
        extra_index=True,
        description="Name of the Kubernetes cluster containing this StorageClass.",
    )
    provisioner: PropertyRef = PropertyRef(
        "provisioner",
        extra_index=True,
        description="Volume plugin or CSI driver used to provision volumes.",
    )
    reclaim_policy: PropertyRef = PropertyRef(
        "reclaim_policy",
        description="Reclaim policy applied to dynamically provisioned volumes.",
    )
    volume_binding_mode: PropertyRef = PropertyRef(
        "volume_binding_mode",
        description="When volume binding and dynamic provisioning occur.",
    )
    allow_volume_expansion: PropertyRef = PropertyRef(
        "allow_volume_expansion",
        description="Whether volumes created by this StorageClass can be expanded.",
    )
    parameters: PropertyRef = PropertyRef(
        "parameters",
        description="Provisioner parameters stored as a JSON-encoded object.",
    )
    mount_options: PropertyRef = PropertyRef(
        "mount_options",
        description="Mount options applied to dynamically provisioned volumes.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesStorageClassToClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesStorageClassToClusterRel(CartographyRelSchema):
    target_node_label: str = "KubernetesCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("CLUSTER_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: KubernetesStorageClassToClusterRelProperties = (
        KubernetesStorageClassToClusterRelProperties()
    )


@dataclass(frozen=True)
class KubernetesStorageClassSchema(CartographyNodeSchema):
    "A class used to dynamically provision persistent storage."

    label: str = "KubernetesStorageClass"
    properties: KubernetesStorageClassNodeProperties = (
        KubernetesStorageClassNodeProperties()
    )
    sub_resource_relationship: KubernetesStorageClassToClusterRel = (
        KubernetesStorageClassToClusterRel()
    )


@dataclass(frozen=True)
class KubernetesPersistentVolumeNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Identifier derived from cluster name and PersistentVolume name.",
    )
    uid: PropertyRef = PropertyRef(
        "uid", description="Kubernetes UID of the PersistentVolume."
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Name of the PersistentVolume."
    )
    creation_timestamp: PropertyRef = PropertyRef(
        "creation_timestamp",
        description="Timestamp when the PersistentVolume was created.",
    )
    deletion_timestamp: PropertyRef = PropertyRef(
        "deletion_timestamp",
        description="Timestamp when the PersistentVolume was marked for deletion.",
    )
    cluster_name: PropertyRef = PropertyRef(
        "CLUSTER_NAME",
        set_in_kwargs=True,
        extra_index=True,
        description="Name of the Kubernetes cluster containing this PersistentVolume.",
    )
    capacity_storage: PropertyRef = PropertyRef(
        "capacity_storage",
        description="Storage capacity reported by `spec.capacity.storage`.",
    )
    capacity_storage_bytes: PropertyRef = PropertyRef(
        "capacity_storage_bytes",
        description="Storage capacity in bytes.",
    )
    access_modes: PropertyRef = PropertyRef(
        "access_modes",
        description="Ways the volume can be mounted, such as ReadWriteOnce or ReadWriteMany.",
    )
    reclaim_policy: PropertyRef = PropertyRef(
        "reclaim_policy",
        description="What happens to the volume after its claim is released.",
    )
    storage_class_name: PropertyRef = PropertyRef(
        "storage_class_name",
        extra_index=True,
        description="Name of the StorageClass associated with the volume.",
    )
    volume_mode: PropertyRef = PropertyRef(
        "volume_mode",
        description="Whether the volume is exposed as a filesystem or block device.",
    )
    phase: PropertyRef = PropertyRef(
        "phase", extra_index=True, description="Current PersistentVolume phase."
    )
    claim_namespace: PropertyRef = PropertyRef(
        "claim_namespace",
        description="Namespace of the bound PersistentVolumeClaim, when present.",
    )
    claim_name: PropertyRef = PropertyRef(
        "claim_name",
        description="Name of the bound PersistentVolumeClaim, when present.",
    )
    csi_driver: PropertyRef = PropertyRef(
        "csi_driver",
        extra_index=True,
        description="CSI driver that manages the volume, when the volume uses CSI.",
    )
    csi_volume_handle: PropertyRef = PropertyRef(
        "csi_volume_handle",
        description="CSI driver volume handle for the backing storage resource.",
    )
    aws_ebs_volume_id: PropertyRef = PropertyRef(
        "aws_ebs_volume_id",
        description="AWS EBS volume ID when managed by the AWS EBS CSI driver.",
    )
    azure_disk_id: PropertyRef = PropertyRef(
        "azure_disk_id",
        description="Azure managed disk resource ID when managed by the Azure Disk CSI driver.",
    )
    labels: PropertyRef = PropertyRef(
        "labels",
        description="PersistentVolume metadata labels stored as a JSON-encoded object.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesPersistentVolumeToClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesPersistentVolumeToClusterRel(CartographyRelSchema):
    target_node_label: str = "KubernetesCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("CLUSTER_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: KubernetesPersistentVolumeToClusterRelProperties = (
        KubernetesPersistentVolumeToClusterRelProperties()
    )


@dataclass(frozen=True)
class KubernetesPersistentVolumeToStorageClassRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesPersistentVolumeToStorageClassRel(CartographyRelSchema):
    target_node_label: str = "KubernetesStorageClass"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("storage_class_id")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_STORAGE_CLASS"
    properties: KubernetesPersistentVolumeToStorageClassRelProperties = (
        KubernetesPersistentVolumeToStorageClassRelProperties()
    )


@dataclass(frozen=True)
class KubernetesPersistentVolumeToCloudDiskRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesPersistentVolumeToAWSEBSVolumeRel(CartographyRelSchema):
    """Links a PersistentVolume to its backing AWS EBS volume."""

    target_node_label: str = "AWSEBSVolume"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("aws_ebs_volume_id")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "BACKED_BY"
    properties: KubernetesPersistentVolumeToCloudDiskRelProperties = (
        KubernetesPersistentVolumeToCloudDiskRelProperties()
    )


@dataclass(frozen=True)
class KubernetesPersistentVolumeToAzureDiskRel(CartographyRelSchema):
    """Links a PersistentVolume to its backing Azure managed disk."""

    target_node_label: str = "AzureDisk"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("azure_disk_id", ignore_case=True)}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "BACKED_BY"
    properties: KubernetesPersistentVolumeToCloudDiskRelProperties = (
        KubernetesPersistentVolumeToCloudDiskRelProperties()
    )


@dataclass(frozen=True)
class KubernetesPersistentVolumeSchema(CartographyNodeSchema):
    "Cluster-scoped persistent storage available to Kubernetes workloads."

    label: str = "KubernetesPersistentVolume"
    properties: KubernetesPersistentVolumeNodeProperties = (
        KubernetesPersistentVolumeNodeProperties()
    )
    sub_resource_relationship: KubernetesPersistentVolumeToClusterRel = (
        KubernetesPersistentVolumeToClusterRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            KubernetesPersistentVolumeToStorageClassRel(),
            KubernetesPersistentVolumeToAWSEBSVolumeRel(),
            KubernetesPersistentVolumeToAzureDiskRel(),
        ]
    )


@dataclass(frozen=True)
class KubernetesPersistentVolumeClaimNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Identifier derived from cluster name, namespace, and claim name.",
    )
    uid: PropertyRef = PropertyRef(
        "uid", description="Kubernetes UID of the PersistentVolumeClaim."
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Name of the PersistentVolumeClaim."
    )
    creation_timestamp: PropertyRef = PropertyRef(
        "creation_timestamp",
        description="Timestamp when the PersistentVolumeClaim was created.",
    )
    deletion_timestamp: PropertyRef = PropertyRef(
        "deletion_timestamp",
        description="Timestamp when the PersistentVolumeClaim was marked for deletion.",
    )
    namespace: PropertyRef = PropertyRef(
        "namespace",
        extra_index=True,
        description="Namespace containing the PersistentVolumeClaim.",
    )
    cluster_name: PropertyRef = PropertyRef(
        "CLUSTER_NAME",
        set_in_kwargs=True,
        extra_index=True,
        description="Name of the Kubernetes cluster containing this claim.",
    )
    storage_class_name: PropertyRef = PropertyRef(
        "storage_class_name",
        extra_index=True,
        description="Name of the StorageClass requested by the claim.",
    )
    volume_name: PropertyRef = PropertyRef(
        "volume_name",
        description="Name of the PersistentVolume bound to the claim.",
    )
    access_modes: PropertyRef = PropertyRef(
        "access_modes",
        description="Requested volume access modes.",
    )
    requested_storage: PropertyRef = PropertyRef(
        "requested_storage",
        description="Storage quantity requested by the claim.",
    )
    requested_storage_bytes: PropertyRef = PropertyRef(
        "requested_storage_bytes",
        description="Storage requested by the claim in bytes.",
    )
    volume_mode: PropertyRef = PropertyRef(
        "volume_mode",
        description="Whether the claim requests a filesystem or block device.",
    )
    phase: PropertyRef = PropertyRef(
        "phase", extra_index=True, description="Current PersistentVolumeClaim phase."
    )
    labels: PropertyRef = PropertyRef(
        "labels",
        description="PersistentVolumeClaim metadata labels stored as a JSON-encoded object.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesPersistentVolumeClaimToClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesPersistentVolumeClaimToClusterRel(CartographyRelSchema):
    target_node_label: str = "KubernetesCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("CLUSTER_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: KubernetesPersistentVolumeClaimToClusterRelProperties = (
        KubernetesPersistentVolumeClaimToClusterRelProperties()
    )


@dataclass(frozen=True)
class KubernetesPersistentVolumeClaimToNamespaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesPersistentVolumeClaimToNamespaceRel(CartographyRelSchema):
    target_node_label: str = "KubernetesNamespace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "cluster_name": PropertyRef("CLUSTER_NAME", set_in_kwargs=True),
            "name": PropertyRef("namespace"),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: KubernetesPersistentVolumeClaimToNamespaceRelProperties = (
        KubernetesPersistentVolumeClaimToNamespaceRelProperties()
    )


@dataclass(frozen=True)
class KubernetesPersistentVolumeClaimToVolumeRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesPersistentVolumeClaimToVolumeRel(CartographyRelSchema):
    target_node_label: str = "KubernetesPersistentVolume"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("volume_id")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "BOUND_TO"
    properties: KubernetesPersistentVolumeClaimToVolumeRelProperties = (
        KubernetesPersistentVolumeClaimToVolumeRelProperties()
    )


@dataclass(frozen=True)
class KubernetesPersistentVolumeClaimToStorageClassRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesPersistentVolumeClaimToStorageClassRel(CartographyRelSchema):
    target_node_label: str = "KubernetesStorageClass"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("storage_class_id")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_STORAGE_CLASS"
    properties: KubernetesPersistentVolumeClaimToStorageClassRelProperties = (
        KubernetesPersistentVolumeClaimToStorageClassRelProperties()
    )


@dataclass(frozen=True)
class KubernetesPersistentVolumeClaimSchema(CartographyNodeSchema):
    "A namespace-scoped request for persistent storage."

    label: str = "KubernetesPersistentVolumeClaim"
    properties: KubernetesPersistentVolumeClaimNodeProperties = (
        KubernetesPersistentVolumeClaimNodeProperties()
    )
    sub_resource_relationship: KubernetesPersistentVolumeClaimToClusterRel = (
        KubernetesPersistentVolumeClaimToClusterRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            KubernetesPersistentVolumeClaimToNamespaceRel(),
            KubernetesPersistentVolumeClaimToVolumeRel(),
            KubernetesPersistentVolumeClaimToStorageClassRel(),
        ]
    )
