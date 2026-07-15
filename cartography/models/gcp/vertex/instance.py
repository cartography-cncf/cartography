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
class GCPVertexAIWorkbenchInstanceNodeProperties(CartographyNodeProperties):
    """
    Properties for a Vertex AI Workbench Instance node.
    See: https://cloud.google.com/vertex-ai/docs/workbench/reference/rest/v2/projects.locations.instances

    Note: This uses the Notebooks API v2, which is used by the GCP Console for creating new Workbench instances.
    The v1 API is deprecated. Fields display_name, description, and notebook_runtime_type are set to None
    as these don't exist in the v2 API schema. These properties are retained for backward compatibility
    but will be null for all Workbench instances.
    """

    id: PropertyRef = PropertyRef(
        "id", extra_index=True, description="Stable identifier for this resource."
    )  # Full resource name
    name: PropertyRef = PropertyRef(
        "name", description="Same as `id`."
    )  # Resource name (same as id)
    display_name: PropertyRef = PropertyRef(
        "display_name",
        description="Human-readable name shown for this resource.",
    )  # None for Workbench Instances
    description: PropertyRef = PropertyRef(
        "description",
        description="Description configured for this resource.",
    )  # None for Workbench Instances
    runtime_user: PropertyRef = PropertyRef(
        "runtime_user",
        description="User identity configured to run the Vertex AI Workbench instance.",
    )  # From creator field (v2 API)
    notebook_runtime_type: PropertyRef = PropertyRef(
        "notebook_runtime_type",
        description="Workbench runtime type reported by the Notebooks API.",
    )  # None for Workbench Instances
    create_time: PropertyRef = PropertyRef(
        "create_time", description="Timestamp when the instance was created."
    )
    update_time: PropertyRef = PropertyRef(
        "update_time", description="Timestamp when the instance was last updated."
    )
    state: PropertyRef = PropertyRef(
        "state", description="The state of the instance (e.g., `ACTIVE`, `STOPPED`)."
    )
    health_state: PropertyRef = PropertyRef(
        "health_state",
        description="The health state of the instance (e.g., `HEALTHY`).",
    )
    service_account: PropertyRef = PropertyRef(
        "service_account",
        description="Service account identity configured for this Vertex AI resource.",
    )  # From gceSetup.serviceAccounts
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )


@dataclass(frozen=True)
class GCPVertexAIWorkbenchInstanceToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
# (:GCPProject)-[:RESOURCE]->(:GCPVertexAIWorkbenchInstance)
class GCPVertexAIWorkbenchInstanceToProjectRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPVertexAIWorkbenchInstanceToProjectRelProperties = (
        GCPVertexAIWorkbenchInstanceToProjectRelProperties()
    )


@dataclass(frozen=True)
class GCPVertexAIWorkbenchInstanceToServiceAccountRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
# (:GCPVertexAIWorkbenchInstance)-[:USES_SERVICE_ACCOUNT]->(:GCPServiceAccount)
class GCPVertexAIWorkbenchInstanceToServiceAccountRel(CartographyRelSchema):
    target_node_label: str = "GCPServiceAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"email": PropertyRef("service_account")}  # Match by email
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_SERVICE_ACCOUNT"
    properties: GCPVertexAIWorkbenchInstanceToServiceAccountRelProperties = (
        GCPVertexAIWorkbenchInstanceToServiceAccountRelProperties()
    )


@dataclass(frozen=True)
class GCPVertexAIWorkbenchInstanceSchema(CartographyNodeSchema):
    """Representation of a GCP [Vertex AI Workbench Instance](https://cloud.google.com/vertex-ai/docs/workbench/reference/rest/v2/projects.locations.instances) (v2 API)."""

    label: str = "GCPVertexAIWorkbenchInstance"
    properties: GCPVertexAIWorkbenchInstanceNodeProperties = (
        GCPVertexAIWorkbenchInstanceNodeProperties()
    )
    sub_resource_relationship: GCPVertexAIWorkbenchInstanceToProjectRel = (
        GCPVertexAIWorkbenchInstanceToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GCPVertexAIWorkbenchInstanceToServiceAccountRel(),
        ]
    )
