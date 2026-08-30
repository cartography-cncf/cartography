from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.ontology.labels import COMPUTE_INSTANCE


@dataclass(frozen=True)
class FlyMachineNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Fly Machine ID.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Machine name."
    )
    state: PropertyRef = PropertyRef("state", description="Machine state.")
    region: PropertyRef = PropertyRef("region", description="Fly.io region.")
    instance_id: PropertyRef = PropertyRef(
        "instance_id", description="Fly Machine instance ID."
    )
    private_ip: PropertyRef = PropertyRef(
        "private_ip", description="Machine private IPv6 address."
    )
    image: PropertyRef = PropertyRef("image", description="Configured image string.")
    image_registry: PropertyRef = PropertyRef(
        "image_registry", description="Image registry."
    )
    image_repository: PropertyRef = PropertyRef(
        "image_repository", description="Image repository."
    )
    image_tag: PropertyRef = PropertyRef("image_tag", description="Image tag.")
    image_digest: PropertyRef = PropertyRef("image_digest", description="Image digest.")
    # NOTE: no `image_id` property here. It exists in the transformed row purely
    # so FlyMachineToImageRel's matcher can resolve HAS_IMAGE - not as a node
    # property, to avoid it as a second, redundant source of truth for the same
    # relationship target the edge itself already encodes.
    cpu_kind: PropertyRef = PropertyRef("cpu_kind", description="Machine CPU kind.")
    cpus: PropertyRef = PropertyRef("cpus", description="Number of CPUs.")
    memory_mb: PropertyRef = PropertyRef("memory_mb", description="Memory size in MB.")
    restart_policy: PropertyRef = PropertyRef(
        "restart_policy", description="Restart policy."
    )
    restart_max_retries: PropertyRef = PropertyRef(
        "restart_max_retries", description="Maximum restart retries."
    )
    process_group: PropertyRef = PropertyRef(
        "process_group", description="Fly process group."
    )
    release_id: PropertyRef = PropertyRef("release_id", description="Fly release ID.")
    release_version: PropertyRef = PropertyRef(
        "release_version", description="Fly release version."
    )
    host_status: PropertyRef = PropertyRef("host_status", description="Host status.")
    cordoned: PropertyRef = PropertyRef(
        "cordoned", description="Whether the Machine is cordoned."
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Creation timestamp."
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="Last update timestamp."
    )
    app_id: PropertyRef = PropertyRef(
        "APP_ID", set_in_kwargs=True, description="Fly app ID."
    )


@dataclass(frozen=True)
class FlyMachineToAppRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:FlyApp)-[:RESOURCE]->(:FlyMachine)
class FlyMachineToAppRel(CartographyRelSchema):
    """Connects `FlyApp` to `FlyMachine` through `RESOURCE`."""

    target_node_label: str = "FlyApp"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("APP_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: FlyMachineToAppRelProperties = FlyMachineToAppRelProperties()


@dataclass(frozen=True)
class FlyMachineToReleaseRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:FlyMachine)-[:DEPLOYED_FROM]->(:FlyRelease)
class FlyMachineToReleaseRel(CartographyRelSchema):
    """Connects `FlyMachine` to the Fly release that deployed it."""

    target_node_label: str = "FlyRelease"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("release_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "DEPLOYED_FROM"
    properties: FlyMachineToReleaseRelProperties = FlyMachineToReleaseRelProperties()


@dataclass(frozen=True)
class FlyMachineToImageRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:FlyMachine)-[:HAS_IMAGE]->(:FlyImage)
class FlyMachineToImageRel(CartographyRelSchema):
    """Connects `FlyMachine` to the `FlyImage` it runs, matched by the app-scoped
    image id (not digest: digest alone is no longer unique once FlyImage is
    scoped per-app, so matching on it would also link to other apps' images
    sharing that digest)."""

    target_node_label: str = "FlyImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("image_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_IMAGE"
    properties: FlyMachineToImageRelProperties = FlyMachineToImageRelProperties()


@dataclass(frozen=True)
class FlyMachineSchema(CartographyNodeSchema):
    """Represents a Fly Machine."""

    label: str = "FlyMachine"
    properties: FlyMachineNodeProperties = FlyMachineNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([COMPUTE_INSTANCE])
    sub_resource_relationship: FlyMachineToAppRel = FlyMachineToAppRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [FlyMachineToReleaseRel(), FlyMachineToImageRel()],
    )
