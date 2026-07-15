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


@dataclass(frozen=True)
class ScalewayFileSystemProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="ID of the file system.")
    name: PropertyRef = PropertyRef("name", description="Name of the file system.")
    size: PropertyRef = PropertyRef(
        "size", description="Size of the file system in bytes."
    )
    status: PropertyRef = PropertyRef(
        "status", description="Status of the file system."
    )
    tags: PropertyRef = PropertyRef(
        "tags", description="Tags attached to the file system."
    )
    number_of_attachments: PropertyRef = PropertyRef(
        "number_of_attachments", description="Number of resources it is attached to."
    )
    region: PropertyRef = PropertyRef(
        "region", description="Region the file system lives in."
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Creation timestamp."
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="Last update timestamp."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Timestamp of the last update"
    )


@dataclass(frozen=True)
class ScalewayFileSystemToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewayFileSystem)
class ScalewayFileSystemToProjectRel(CartographyRelSchema):
    """Connects `ScalewayProject` to `ScalewayFileSystem` through `RESOURCE`."""

    target_node_label: str = "ScalewayProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ScalewayFileSystemToProjectRelProperties = (
        ScalewayFileSystemToProjectRelProperties()
    )


@dataclass(frozen=True)
class ScalewayFileSystemSchema(CartographyNodeSchema):
    """Represents a File Storage file system in Scaleway."""

    label: str = "ScalewayFileSystem"
    # FileStorage label is used for cross-provider ontology mapping.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["FileStorage"])
    properties: ScalewayFileSystemProperties = ScalewayFileSystemProperties()
    sub_resource_relationship: ScalewayFileSystemToProjectRel = (
        ScalewayFileSystemToProjectRel()
    )
