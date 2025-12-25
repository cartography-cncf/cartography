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
class GCPVertexAIDeployedModelNodeProperties(CartographyNodeProperties):
    """
    Properties for a Vertex AI Deployed Model node.
    See: https://cloud.google.com/vertex-ai/docs/reference/rest/v1/projects.locations.endpoints#DeployedModel
    """

    id: PropertyRef = PropertyRef("id", extra_index=True)
    deployed_model_id: PropertyRef = PropertyRef("deployed_model_id")
    model: PropertyRef = PropertyRef("model")  # Reference to the model resource name
    display_name: PropertyRef = PropertyRef("display_name")
    create_time: PropertyRef = PropertyRef("create_time")
    service_account: PropertyRef = PropertyRef("service_account")
    enable_access_logging: PropertyRef = PropertyRef("enable_access_logging")
    endpoint_id: PropertyRef = PropertyRef("endpoint_id")  # For SERVES relationship
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPVertexAIDeployedModelToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:GCPProject)-[:RESOURCE]->(:GCPVertexAIDeployedModel)
class GCPVertexAIDeployedModelToProjectRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPVertexAIDeployedModelToProjectRelProperties = (
        GCPVertexAIDeployedModelToProjectRelProperties()
    )


@dataclass(frozen=True)
class GCPVertexAIDeployedModelToEndpointRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:GCPVertexAIEndpoint)-[:SERVES]->(:GCPVertexAIDeployedModel)
class GCPVertexAIDeployedModelToEndpointRel(CartographyRelSchema):
    target_node_label: str = "GCPVertexAIEndpoint"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("endpoint_id")}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "SERVES"
    properties: GCPVertexAIDeployedModelToEndpointRelProperties = (
        GCPVertexAIDeployedModelToEndpointRelProperties()
    )


@dataclass(frozen=True)
class GCPVertexAIDeployedModelToModelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:GCPVertexAIDeployedModel)-[:INSTANCE_OF]->(:GCPVertexAIModel)
class GCPVertexAIDeployedModelToModelRel(CartographyRelSchema):
    target_node_label: str = "GCPVertexAIModel"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("model")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "INSTANCE_OF"
    properties: GCPVertexAIDeployedModelToModelRelProperties = (
        GCPVertexAIDeployedModelToModelRelProperties()
    )


@dataclass(frozen=True)
class GCPVertexAIDeployedModelSchema(CartographyNodeSchema):
    label: str = "GCPVertexAIDeployedModel"
    properties: GCPVertexAIDeployedModelNodeProperties = (
        GCPVertexAIDeployedModelNodeProperties()
    )
    sub_resource_relationship: GCPVertexAIDeployedModelToProjectRel = (
        GCPVertexAIDeployedModelToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GCPVertexAIDeployedModelToEndpointRel(),
            GCPVertexAIDeployedModelToModelRel(),
        ]
    )
