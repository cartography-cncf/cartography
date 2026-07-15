from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class GCPKeyRingProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="The full resource name of the Key Ring."
    )
    name: PropertyRef = PropertyRef(
        "name", description="The short name of the Key Ring."
    )
    location: PropertyRef = PropertyRef(
        "location", description="The GCP location of the Key Ring."
    )
    project_id: PropertyRef = PropertyRef(
        "project_id", description="Google Cloud project that owns this resource."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="The timestamp of the last update.",
    )


@dataclass(frozen=True)
class GCPKeyRingToGCPProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
class GCPKeyRingToGCPProjectRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPKeyRingToGCPProjectRelProperties = (
        GCPKeyRingToGCPProjectRelProperties()
    )


@dataclass(frozen=True)
class GCPKeyRingSchema(CartographyNodeSchema):
    """Representation of a GCP [Key Ring](https://cloud.google.com/kms/docs/reference/rest/v1/projects.locations.keyRings)."""

    label: str = "GCPKeyRing"
    properties: GCPKeyRingProperties = GCPKeyRingProperties()
    sub_resource_relationship: GCPKeyRingToGCPProjectRel = GCPKeyRingToGCPProjectRel()
