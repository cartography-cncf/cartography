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
class GCPVertexAIDatasetNodeProperties(CartographyNodeProperties):
    """
    Properties for a Vertex AI Dataset node.
    See: https://cloud.google.com/vertex-ai/docs/reference/rest/v1/projects.locations.datasets
    """

    id: PropertyRef = PropertyRef(
        "id", extra_index=True, description="Stable identifier for this resource."
    )  # Full resource name
    name: PropertyRef = PropertyRef(
        "name", description="Same as `id`."
    )  # Resource name (same as id)
    display_name: PropertyRef = PropertyRef(
        "display_name", description="User-provided display name of the dataset."
    )
    description: PropertyRef = PropertyRef(
        "description", description="Description configured for this resource."
    )
    labels: PropertyRef = PropertyRef(
        "labels", description="Key-value labels attached to this resource."
    )
    create_time: PropertyRef = PropertyRef(
        "create_time", description="Timestamp when the dataset was created."
    )
    update_time: PropertyRef = PropertyRef(
        "update_time", description="Timestamp when the dataset was last updated."
    )
    etag: PropertyRef = PropertyRef(
        "etag", description="Used to perform consistent read-modify-write updates."
    )
    data_item_count: PropertyRef = PropertyRef(
        "data_item_count", description="The number of data items in the dataset."
    )
    metadata_schema_uri: PropertyRef = PropertyRef(
        "metadata_schema_uri", description="The metadata schema URI for the dataset."
    )
    metadata: PropertyRef = PropertyRef(
        "metadata", description="JSON string with dataset metadata."
    )
    encryption_spec: PropertyRef = PropertyRef(
        "encryption_spec", description="JSON string with encryption configuration."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )


@dataclass(frozen=True)
class GCPVertexAIDatasetToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
# (:GCPProject)-[:RESOURCE]->(:GCPVertexAIDataset)
class GCPVertexAIDatasetToProjectRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPVertexAIDatasetToProjectRelProperties = (
        GCPVertexAIDatasetToProjectRelProperties()
    )


@dataclass(frozen=True)
class GCPVertexAIDatasetSchema(CartographyNodeSchema):
    """Representation of a GCP [Vertex AI Dataset](https://cloud.google.com/vertex-ai/docs/reference/rest/v1/projects.locations.datasets)."""

    label: str = "GCPVertexAIDataset"
    properties: GCPVertexAIDatasetNodeProperties = GCPVertexAIDatasetNodeProperties()
    sub_resource_relationship: GCPVertexAIDatasetToProjectRel = (
        GCPVertexAIDatasetToProjectRel()
    )
