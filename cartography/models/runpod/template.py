from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.runpod._relationships import RunPodResourceRelProperties
from cartography.models.runpod._relationships import RunPodToAccountRel


@dataclass(frozen=True)
class RunPodTemplateNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="ID of the RunPod template.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    account_id: PropertyRef = PropertyRef(
        "account_id", description="Configured RunPod account identifier."
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Display name of the template."
    )
    image_name: PropertyRef = PropertyRef("image_name", description="Container image.")
    container_disk_in_gb: PropertyRef = PropertyRef(
        "container_disk_in_gb", description="Container disk size in GiB."
    )
    volume_in_gb: PropertyRef = PropertyRef(
        "volume_in_gb", description="Persistent volume size in GiB."
    )
    volume_mount_path: PropertyRef = PropertyRef(
        "volume_mount_path", description="Persistent volume mount path."
    )
    registry_id: PropertyRef = PropertyRef(
        "registry_id", extra_index=True, description="Registry credential ID, if any."
    )
    is_public: PropertyRef = PropertyRef(
        "is_public", description="Whether the template is public."
    )
    is_serverless: PropertyRef = PropertyRef(
        "is_serverless", description="Whether the template is serverless-compatible."
    )
    category: PropertyRef = PropertyRef("category", description="Template category.")
    start_ssh: PropertyRef = PropertyRef(
        "start_ssh", description="Whether the template starts SSH."
    )
    start_jupyter: PropertyRef = PropertyRef(
        "start_jupyter", description="Whether the template starts Jupyter."
    )
    ports: PropertyRef = PropertyRef("ports", description="Configured port summaries.")


@dataclass(frozen=True)
class RunPodTemplateToRegistryCredentialRel(CartographyRelSchema):
    """Connects a template to the registry credential used for its image."""

    target_node_label: str = "RunPodRegistryCredential"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("registry_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_REGISTRY_CREDENTIAL"
    properties: RunPodResourceRelProperties = RunPodResourceRelProperties()


@dataclass(frozen=True)
class RunPodTemplateSchema(CartographyNodeSchema):
    """A RunPod template used to configure pods or serverless endpoints."""

    label: str = "RunPodTemplate"
    properties: RunPodTemplateNodeProperties = RunPodTemplateNodeProperties()
    sub_resource_relationship: RunPodToAccountRel = RunPodToAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [RunPodTemplateToRegistryCredentialRel()],
    )
