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
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    created_at: PropertyRef = PropertyRef("created_at")
    # Raw CLOUD_PROVIDER_* value: AWS, GCP, OCI or AUTO. This is the provider the share is
    # backed by, not a region.
    cloud_provider: PropertyRef = PropertyRef("cloud_provider", extra_index=True)
    environment_name: PropertyRef = PropertyRef("environment_name", extra_index=True)


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
    label: str = "ModalNetworkFileSystem"
    properties: ModalNetworkFileSystemNodeProperties = (
        ModalNetworkFileSystemNodeProperties()
    )
    sub_resource_relationship: ModalNetworkFileSystemToEnvironmentRel = (
        ModalNetworkFileSystemToEnvironmentRel()
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([FILE_STORAGE])
