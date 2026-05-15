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

    id: PropertyRef = PropertyRef("id", extra_index=True)  # Full resource name
    name: PropertyRef = PropertyRef("name")  # Resource name (same as id)
    display_name: PropertyRef = PropertyRef("display_name")
    create_time: PropertyRef = PropertyRef("create_time")
    update_time: PropertyRef = PropertyRef("update_time")
    start_time: PropertyRef = PropertyRef("start_time")
    end_time: PropertyRef = PropertyRef("end_time")
    state: PropertyRef = PropertyRef("state")
    error: PropertyRef = PropertyRef("error")
    model_to_upload: PropertyRef = PropertyRef("model_to_upload")  # Model produced
    training_task_definition: PropertyRef = PropertyRef("training_task_definition")
    # Relationship matcher properties
    dataset_id: PropertyRef = PropertyRef(
        "dataset_id"
    )  # For READS_FROM Dataset relationship
    model_id: PropertyRef = PropertyRef("model_id")  # For PRODUCES Model relationship
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPVertexAITrainingPipelineToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


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
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


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
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


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
