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
class GCPVertexAIEndpointNodeProperties(CartographyNodeProperties):
    """
    Properties for a Vertex AI Endpoint node.
    See: https://cloud.google.com/vertex-ai/docs/reference/rest/v1/projects.locations.endpoints
    """

    id: PropertyRef = PropertyRef(
        "id", extra_index=True, description="Stable identifier for this resource."
    )  # Full resource name
    name: PropertyRef = PropertyRef(
        "name", description="Same as `id`."
    )  # Resource name (same as id)
    display_name: PropertyRef = PropertyRef(
        "display_name", description="User-provided display name of the endpoint."
    )
    description: PropertyRef = PropertyRef(
        "description", description="Description of the endpoint."
    )
    create_time: PropertyRef = PropertyRef(
        "create_time", description="Timestamp when the endpoint was created."
    )
    update_time: PropertyRef = PropertyRef(
        "update_time", description="Timestamp when the endpoint was last updated."
    )
    etag: PropertyRef = PropertyRef(
        "etag", description="Used to perform consistent read-modify-write updates."
    )
    labels: PropertyRef = PropertyRef(
        "labels", description="Key-value labels attached to this resource."
    )
    network: PropertyRef = PropertyRef(
        "network",
        description="The full name of the Google Compute Engine network to which the endpoint should be peered.",
    )  # VPC network
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )


@dataclass(frozen=True)
class GCPVertexAIEndpointToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
# (:GCPProject)-[:RESOURCE]->(:GCPVertexAIEndpoint)
class GCPVertexAIEndpointToProjectRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPVertexAIEndpointToProjectRelProperties = (
        GCPVertexAIEndpointToProjectRelProperties()
    )


@dataclass(frozen=True)
class GCPVertexAIEndpointSchema(CartographyNodeSchema):
    """Representation of a GCP [Vertex AI Endpoint](https://cloud.google.com/vertex-ai/docs/reference/rest/v1/projects.locations.endpoints)."""

    label: str = "GCPVertexAIEndpoint"
    properties: GCPVertexAIEndpointNodeProperties = GCPVertexAIEndpointNodeProperties()
    sub_resource_relationship: GCPVertexAIEndpointToProjectRel = (
        GCPVertexAIEndpointToProjectRel()
    )
