from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class GCPVertexAITrainingPipelineNodeProperties(CartographyNodeProperties):
    """
    Properties for a Vertex AI Training Pipeline node.
    See: https://cloud.google.com/vertex-ai/docs/reference/rest/v1/projects.locations.trainingPipelines
    """

    id: PropertyRef = PropertyRef(
        "id", extra_index=True, description="Stable identifier for this resource."
    )  # Full resource name
    name: PropertyRef = PropertyRef(
        "name", description="Same as `id`."
    )  # Resource name (same as id)
    display_name: PropertyRef = PropertyRef(
        "display_name",
        description="User-provided display name of the training pipeline.",
    )
    create_time: PropertyRef = PropertyRef(
        "create_time", description="Timestamp when the pipeline was created."
    )
    update_time: PropertyRef = PropertyRef(
        "update_time", description="Timestamp when the pipeline was last updated."
    )
    start_time: PropertyRef = PropertyRef(
        "start_time", description="Timestamp when the pipeline started running."
    )
    end_time: PropertyRef = PropertyRef(
        "end_time", description="Timestamp when the pipeline finished."
    )
    state: PropertyRef = PropertyRef(
        "state",
        description="The state of the pipeline (e.g., `PIPELINE_STATE_SUCCEEDED`).",
    )
    error: PropertyRef = PropertyRef(
        "error",
        description="JSON string with error information if the pipeline failed.",
    )
    model_to_upload: PropertyRef = PropertyRef(
        "model_to_upload",
        description="JSON string describing the model that was uploaded.",
    )  # Model produced
    training_task_definition: PropertyRef = PropertyRef(
        "training_task_definition",
        description="The training task definition schema URI.",
    )
    # Relationship matcher properties
    dataset_id: PropertyRef = PropertyRef(
        "dataset_id",
        description="Full resource name of the Dataset used for training (used for relationships).",
    )  # For READS_FROM Dataset relationship
    model_id: PropertyRef = PropertyRef(
        "model_id",
        description="Full resource name of the Model produced by training (used for relationships).",
    )  # For PRODUCES Model relationship
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )


@dataclass(frozen=True)
class GCPVertexAITrainingPipelineToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
# (:GCPProject)-[:RESOURCE]->(:GCPVertexAITrainingPipeline)
class GCPVertexAITrainingPipelineToProjectRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPVertexAITrainingPipelineToProjectRelProperties = (
        GCPVertexAITrainingPipelineToProjectRelProperties()
    )


@dataclass(frozen=True)
class GCPVertexAITrainingPipelineToDatasetRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
# (:GCPVertexAITrainingPipeline)-[:READS_FROM]->(:GCPVertexAIDataset)
class GCPVertexAITrainingPipelineToDatasetRel(CartographyRelSchema):
    target_node_label: str = "GCPVertexAIDataset"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("dataset_id")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "READS_FROM"
    properties: GCPVertexAITrainingPipelineToDatasetRelProperties = (
        GCPVertexAITrainingPipelineToDatasetRelProperties()
    )


@dataclass(frozen=True)
class GCPVertexAITrainingPipelineToModelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
# (:GCPVertexAITrainingPipeline)-[:PRODUCES]->(:GCPVertexAIModel)
class GCPVertexAITrainingPipelineToModelRel(CartographyRelSchema):
    target_node_label: str = "GCPVertexAIModel"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("model_id")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "PRODUCES"
    properties: GCPVertexAITrainingPipelineToModelRelProperties = (
        GCPVertexAITrainingPipelineToModelRelProperties()
    )


@dataclass(frozen=True)
class GCPVertexAITrainingPipelineSchema(CartographyNodeSchema):
    """Representation of a GCP [Vertex AI Training Pipeline](https://cloud.google.com/vertex-ai/docs/reference/rest/v1/projects.locations.trainingPipelines)."""

    label: str = "GCPVertexAITrainingPipeline"
    properties: GCPVertexAITrainingPipelineNodeProperties = (
        GCPVertexAITrainingPipelineNodeProperties()
    )
    sub_resource_relationship: GCPVertexAITrainingPipelineToProjectRel = (
        GCPVertexAITrainingPipelineToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GCPVertexAITrainingPipelineToDatasetRel(),
            GCPVertexAITrainingPipelineToModelRel(),
        ]
    )
