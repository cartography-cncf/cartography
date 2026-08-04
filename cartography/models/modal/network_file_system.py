from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.ontology.labels import FILE_STORAGE


@dataclass(frozen=True)
class ModalNetworkFileSystemNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Share ID, e.g. `sv-1AsDfGhJkLzXcVbNmQwErT`."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", extra_index=True, description="Share name.")
    created_at: PropertyRef = PropertyRef(
        "created_at", description="When the share was created."
    )
    # Raw CLOUD_PROVIDER_* value: AWS, GCP, OCI or AUTO. This is the provider the share is
    # backed by, not a region.
    cloud_provider: PropertyRef = PropertyRef(
        "cloud_provider",
        extra_index=True,
        description="Raw `CLOUD_PROVIDER_*` value: AWS, GCP, OCI or AUTO. This names a provider, not a region, which is why it is not mapped onto the ontology `location` field.",
    )
    environment_name: PropertyRef = PropertyRef(
        "environment_name",
        extra_index=True,
        description="Name of the owning environment.",
    )


@dataclass(frozen=True)
class ModalNetworkFileSystemToEnvironmentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ModalEnvironment)-[:RESOURCE]->(:ModalNetworkFileSystem)
class ModalNetworkFileSystemToEnvironmentRel(CartographyRelSchema):
    target_node_label: str = "ModalEnvironment"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ENVIRONMENT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ModalNetworkFileSystemToEnvironmentRelProperties = (
        ModalNetworkFileSystemToEnvironmentRelProperties()
    )


@dataclass(frozen=True)
# A Modal network file system, Modal's older shared-filesystem primitive, superseded by
# Volume. Still enumerated because existing workspaces have them, and an unnoticed legacy
# share holding data is exactly the kind of thing an inventory should surface.
class ModalNetworkFileSystemSchema(CartographyNodeSchema):
    """Represents a Modal network file system: the older shared-filesystem primitive, superseded by Volume. Still inventoried because existing workspaces have them, and an unnoticed legacy share holding data is exactly what an inventory should surface."""

    label: str = "ModalNetworkFileSystem"
    properties: ModalNetworkFileSystemNodeProperties = (
        ModalNetworkFileSystemNodeProperties()
    )
    sub_resource_relationship: ModalNetworkFileSystemToEnvironmentRel = (
        ModalNetworkFileSystemToEnvironmentRel()
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([FILE_STORAGE])
