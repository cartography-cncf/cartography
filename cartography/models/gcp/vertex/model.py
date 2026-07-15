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


@dataclass(frozen=True)
class GCPVertexAIModelNodeProperties(CartographyNodeProperties):
    """
    Properties for a Vertex AI Model node.
    See: https://cloud.google.com/vertex-ai/docs/reference/rest/v1/projects.locations.models
    """

    id: PropertyRef = PropertyRef(
        "id", extra_index=True, description="Stable identifier for this resource."
    )  # Full resource name
    name: PropertyRef = PropertyRef(
        "name", description="Same as `id`."
    )  # Resource name (same as id)
    display_name: PropertyRef = PropertyRef(
        "display_name", description="User-provided display name of the model."
    )
    description: PropertyRef = PropertyRef(
        "description", description="Description of the model."
    )
    version_id: PropertyRef = PropertyRef(
        "version_id", description="The version ID of the model."
    )
    version_create_time: PropertyRef = PropertyRef(
        "version_create_time",
        description="Timestamp when this model version was created.",
    )
    version_update_time: PropertyRef = PropertyRef(
        "version_update_time",
        description="Timestamp when this model version was last updated.",
    )
    create_time: PropertyRef = PropertyRef(
        "create_time", description="Timestamp when the model was originally created."
    )
    update_time: PropertyRef = PropertyRef(
        "update_time", description="Timestamp when the model was last updated."
    )
    artifact_uri: PropertyRef = PropertyRef(
        "artifact_uri",
        description="The path to the directory containing the Model artifact and supporting files (GCS URI).",
    )  # GCS location
    etag: PropertyRef = PropertyRef(
        "etag", description="Used to perform consistent read-modify-write updates."
    )
    labels: PropertyRef = PropertyRef(
        "labels", description="JSON string of user-defined labels."
    )
    training_pipeline: PropertyRef = PropertyRef(
        "training_pipeline",
        description="Resource name of the Training Pipeline that created this model.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )


@dataclass(frozen=True)
class GCPVertexAIModelToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
# (:GCPProject)-[:RESOURCE]->(:GCPVertexAIModel)
class GCPVertexAIModelToProjectRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPVertexAIModelToProjectRelProperties = (
        GCPVertexAIModelToProjectRelProperties()
    )


@dataclass(frozen=True)
class GCPVertexAIModelToGCSBucketRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
# (:GCPVertexAIModel)-[:STORED_IN]->(:GCSBucket)
class GCPVertexAIModelToGCSBucketRel(CartographyRelSchema):
    target_node_label: str = "GCPBucket"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("gcs_bucket_id")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "STORED_IN"
    properties: GCPVertexAIModelToGCSBucketRelProperties = (
        GCPVertexAIModelToGCSBucketRelProperties()
    )


@dataclass(frozen=True)
class GCPVertexAIModelSchema(CartographyNodeSchema):
    """Representation of a GCP [Vertex AI Model](https://cloud.google.com/vertex-ai/docs/reference/rest/v1/projects.locations.models)."""

    label: str = "GCPVertexAIModel"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["AIModel"])
    properties: GCPVertexAIModelNodeProperties = GCPVertexAIModelNodeProperties()
    sub_resource_relationship: GCPVertexAIModelToProjectRel = (
        GCPVertexAIModelToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GCPVertexAIModelToGCSBucketRel(),
        ]
    )
