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
class GCPVertexAIFeatureGroupNodeProperties(CartographyNodeProperties):
    """
    Properties for a Vertex AI Feature Group node.
    See: https://cloud.google.com/vertex-ai/docs/reference/rest/v1/projects.locations.featureGroups

    Feature Groups are the new architecture for Vertex AI Feature Store, replacing the legacy
    FeatureStore → EntityType → Feature hierarchy. Feature Groups connect directly to BigQuery
    sources and provide feature serving capabilities.
    """

    id: PropertyRef = PropertyRef("id", extra_index=True)  # Full resource name
    name: PropertyRef = PropertyRef("name")  # Resource name (same as id)
    description: PropertyRef = PropertyRef("description")
    labels: PropertyRef = PropertyRef("labels")
    create_time: PropertyRef = PropertyRef("create_time")
    update_time: PropertyRef = PropertyRef("update_time")
    etag: PropertyRef = PropertyRef("etag")
    bigquery_source_uri: PropertyRef = PropertyRef(
        "bigquery_source_uri"
    )  # From bigQuery.bigQuerySource.inputUri
    entity_id_columns: PropertyRef = PropertyRef(
        "entity_id_columns"
    )  # JSON array of entity ID column names
    timestamp_column: PropertyRef = PropertyRef(
        "timestamp_column"
    )  # From bigQuery.timeSeries.timestampColumn
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPVertexAIFeatureGroupToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:GCPProject)-[:RESOURCE]->(:GCPVertexAIFeatureGroup)
class GCPVertexAIFeatureGroupToProjectRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPVertexAIFeatureGroupToProjectRelProperties = (
        GCPVertexAIFeatureGroupToProjectRelProperties()
    )


@dataclass(frozen=True)
class GCPVertexAIFeatureGroupSchema(CartographyNodeSchema):
    label: str = "GCPVertexAIFeatureGroup"
    properties: GCPVertexAIFeatureGroupNodeProperties = (
        GCPVertexAIFeatureGroupNodeProperties()
    )
    sub_resource_relationship: GCPVertexAIFeatureGroupToProjectRel = (
        GCPVertexAIFeatureGroupToProjectRel()
    )
