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

    id: PropertyRef = PropertyRef(
        "id", extra_index=True, description="Stable identifier for this resource."
    )  # Full resource name
    name: PropertyRef = PropertyRef(
        "name", description="Same as `id`."
    )  # Resource name (same as id)
    description: PropertyRef = PropertyRef(
        "description", description="Description configured for this resource."
    )
    labels: PropertyRef = PropertyRef(
        "labels", description="Key-value labels attached to this resource."
    )
    create_time: PropertyRef = PropertyRef(
        "create_time", description="Timestamp when the feature group was created."
    )
    update_time: PropertyRef = PropertyRef(
        "update_time", description="Timestamp when the feature group was last updated."
    )
    etag: PropertyRef = PropertyRef(
        "etag", description="Used to perform consistent read-modify-write updates."
    )
    bigquery_source_uri: PropertyRef = PropertyRef(
        "bigquery_source_uri",
        description="The BigQuery source URI for the feature group.",
    )  # From bigQuery.bigQuerySource.inputUri
    entity_id_columns: PropertyRef = PropertyRef(
        "entity_id_columns",
        description="JSON array of entity ID column names.",
    )  # JSON array of entity ID column names
    timestamp_column: PropertyRef = PropertyRef(
        "timestamp_column",
        description="The timestamp column name (for time series features).",
    )  # From bigQuery.timeSeries.timestampColumn
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )


@dataclass(frozen=True)
class GCPVertexAIFeatureGroupToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


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
    """Representation of a GCP [Vertex AI Feature Group](https://cloud.google.com/vertex-ai/docs/reference/rest/v1/projects.locations.featureGroups). Feature Groups are the new architecture for Vertex AI Feature Store."""

    label: str = "GCPVertexAIFeatureGroup"
    properties: GCPVertexAIFeatureGroupNodeProperties = (
        GCPVertexAIFeatureGroupNodeProperties()
    )
    sub_resource_relationship: GCPVertexAIFeatureGroupToProjectRel = (
        GCPVertexAIFeatureGroupToProjectRel()
    )
