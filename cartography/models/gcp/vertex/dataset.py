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

    id: PropertyRef = PropertyRef("id", extra_index=True)  # Full resource name
    name: PropertyRef = PropertyRef("name")  # Resource name (same as id)
    display_name: PropertyRef = PropertyRef("display_name")
    description: PropertyRef = PropertyRef("description")
    labels: PropertyRef = PropertyRef("labels")
    create_time: PropertyRef = PropertyRef("create_time")
    update_time: PropertyRef = PropertyRef("update_time")
    etag: PropertyRef = PropertyRef("etag")
    data_item_count: PropertyRef = PropertyRef("data_item_count")
    metadata_schema_uri: PropertyRef = PropertyRef("metadata_schema_uri")
    metadata: PropertyRef = PropertyRef("metadata")
    encryption_spec: PropertyRef = PropertyRef("encryption_spec")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPVertexAIDatasetToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


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
    label: str = "GCPVertexAIDataset"
    properties: GCPVertexAIDatasetNodeProperties = GCPVertexAIDatasetNodeProperties()
    sub_resource_relationship: GCPVertexAIDatasetToProjectRel = (
        GCPVertexAIDatasetToProjectRel()
    )
