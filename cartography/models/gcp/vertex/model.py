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
class GCPVertexAIModelNodeProperties(CartographyNodeProperties):
    """
    Properties for a Vertex AI Model node.
    See: https://cloud.google.com/vertex-ai/docs/reference/rest/v1/projects.locations.models
    """

    id: PropertyRef = PropertyRef("id", extra_index=True)  # Full resource name
    name: PropertyRef = PropertyRef("name")  # Resource name (same as id)
    display_name: PropertyRef = PropertyRef("display_name")
    description: PropertyRef = PropertyRef("description")
    version_id: PropertyRef = PropertyRef("version_id")
    version_create_time: PropertyRef = PropertyRef("version_create_time")
    version_update_time: PropertyRef = PropertyRef("version_update_time")
    create_time: PropertyRef = PropertyRef("create_time")
    update_time: PropertyRef = PropertyRef("update_time")
    artifact_uri: PropertyRef = PropertyRef("artifact_uri")  # GCS location
    etag: PropertyRef = PropertyRef("etag")
    labels: PropertyRef = PropertyRef("labels")
    training_pipeline: PropertyRef = PropertyRef("training_pipeline")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPVertexAIModelToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


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
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


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
    label: str = "GCPVertexAIModel"
    properties: GCPVertexAIModelNodeProperties = GCPVertexAIModelNodeProperties()
    sub_resource_relationship: GCPVertexAIModelToProjectRel = (
        GCPVertexAIModelToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GCPVertexAIModelToGCSBucketRel(),
        ]
    )
