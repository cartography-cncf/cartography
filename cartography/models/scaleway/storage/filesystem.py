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
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    size: PropertyRef = PropertyRef("size")
    status: PropertyRef = PropertyRef("status")
    tags: PropertyRef = PropertyRef("tags")
    number_of_attachments: PropertyRef = PropertyRef("number_of_attachments")
    region: PropertyRef = PropertyRef("region")
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ScalewayFileSystemToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewayFileSystem)
class ScalewayFileSystemToProjectRel(CartographyRelSchema):
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
    label: str = "ScalewayFileSystem"
    # FileStorage label is used for cross-provider ontology mapping.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["FileStorage"])
    properties: ScalewayFileSystemProperties = ScalewayFileSystemProperties()
    sub_resource_relationship: ScalewayFileSystemToProjectRel = (
        ScalewayFileSystemToProjectRel()
    )
