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
from cartography.models.runpod._relationships import RunPodResourceRelProperties
from cartography.models.runpod._relationships import RunPodToAccountRel


@dataclass(frozen=True)
class RunPodPodNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="ID of the RunPod pod.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    account_id: PropertyRef = PropertyRef(
        "account_id", description="Configured RunPod account identifier."
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Display name of the pod."
    )
    status: PropertyRef = PropertyRef("status", description="Current pod status.")
    image_name: PropertyRef = PropertyRef("image_name", description="Container image.")
    machine_id: PropertyRef = PropertyRef(
        "machine_id", description="RunPod machine ID."
    )
    data_center_id: PropertyRef = PropertyRef(
        "data_center_id", extra_index=True, description="RunPod data center ID."
    )
    gpu_type_id: PropertyRef = PropertyRef("gpu_type_id", description="GPU type ID.")
    gpu_count: PropertyRef = PropertyRef("gpu_count", description="Number of GPUs.")
    vcpu_count: PropertyRef = PropertyRef("vcpu_count", description="Number of vCPUs.")
    memory_in_gb: PropertyRef = PropertyRef(
        "memory_in_gb", description="Memory in GiB."
    )
    container_disk_in_gb: PropertyRef = PropertyRef(
        "container_disk_in_gb", description="Container disk size in GiB."
    )
    volume_in_gb: PropertyRef = PropertyRef(
        "volume_in_gb", description="Persistent volume size in GiB."
    )
    volume_mount_path: PropertyRef = PropertyRef(
        "volume_mount_path", description="Persistent volume mount path."
    )
    network_volume_id: PropertyRef = PropertyRef(
        "network_volume_id",
        extra_index=True,
        description="Attached RunPod network volume ID, if any.",
    )
    template_id: PropertyRef = PropertyRef(
        "template_id", extra_index=True, description="Template used by this pod."
    )
    registry_id: PropertyRef = PropertyRef(
        "registry_id", extra_index=True, description="Registry credential ID, if any."
    )
    global_networking_enabled: PropertyRef = PropertyRef(
        "global_networking_enabled",
        description="Whether RunPod global networking is enabled for the pod.",
    )
    public_ip: PropertyRef = PropertyRef("public_ip", description="Public IP address.")
    exposed_ports: PropertyRef = PropertyRef(
        "exposed_ports", description="Configured exposed port summaries."
    )
    runtime_ports: PropertyRef = PropertyRef(
        "runtime_ports", description="Runtime exposed port summaries."
    )
    created_at: PropertyRef = PropertyRef("created_at", description="Creation time.")
    started_at: PropertyRef = PropertyRef("started_at", description="Start time.")


@dataclass(frozen=True)
class RunPodPodToNetworkVolumeRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class RunPodPodToNetworkVolumeRel(CartographyRelSchema):
    """Connects a pod to its attached network volume, if any."""

    target_node_label: str = "RunPodNetworkVolume"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("network_volume_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_VOLUME"
    properties: RunPodPodToNetworkVolumeRelProperties = (
        RunPodPodToNetworkVolumeRelProperties()
    )


@dataclass(frozen=True)
class RunPodPodToTemplateRel(CartographyRelSchema):
    """Connects a pod to the template used to create or configure it."""

    target_node_label: str = "RunPodTemplate"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("template_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_TEMPLATE"
    properties: RunPodResourceRelProperties = RunPodResourceRelProperties()


@dataclass(frozen=True)
class RunPodPodToRegistryCredentialRel(CartographyRelSchema):
    """Connects a pod to the registry credential used for its image."""

    target_node_label: str = "RunPodRegistryCredential"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("registry_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_REGISTRY_CREDENTIAL"
    properties: RunPodResourceRelProperties = RunPodResourceRelProperties()


@dataclass(frozen=True)
class RunPodPodToDataCenterRel(CartographyRelSchema):
    """Connects a pod to the data center where it runs."""

    target_node_label: str = "RunPodDataCenter"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("data_center_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RUNS_IN"
    properties: RunPodResourceRelProperties = RunPodResourceRelProperties()


@dataclass(frozen=True)
class RunPodPodSchema(CartographyNodeSchema):
    """A RunPod pod: a GPU container workload running in a RunPod account."""

    label: str = "RunPodPod"
    properties: RunPodPodNodeProperties = RunPodPodNodeProperties()
    sub_resource_relationship: RunPodToAccountRel = RunPodToAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            RunPodPodToNetworkVolumeRel(),
            RunPodPodToTemplateRel(),
            RunPodPodToRegistryCredentialRel(),
            RunPodPodToDataCenterRel(),
        ],
    )
