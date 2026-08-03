from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.databricks.extra_labels import DATABRICKS_ACL_OBJECT


@dataclass(frozen=True)
class DatabricksServingEndpointNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Workspace-scoped identifier for the Databricks serving endpoint.",
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Name of the serving endpoint."
    )
    # System id the Permissions API keys off (distinct from the display name).
    endpoint_id: PropertyRef = PropertyRef(
        "endpoint_id",
        extra_index=True,
        description="System identifier of the serving endpoint.",
    )
    endpoint_type: PropertyRef = PropertyRef(
        "endpoint_type", description="Type of the serving endpoint."
    )
    task: PropertyRef = PropertyRef(
        "task", description="Machine learning task served by the endpoint."
    )
    state_ready: PropertyRef = PropertyRef(
        "state_ready", description="Readiness state of the serving endpoint."
    )
    state_config_update: PropertyRef = PropertyRef(
        "state_config_update",
        description="Configuration update state of the serving endpoint.",
    )
    permission_level: PropertyRef = PropertyRef(
        "permission_level",
        description="Permission level held by the requesting principal.",
    )
    route_optimized: PropertyRef = PropertyRef(
        "route_optimized", description="Whether route optimization is enabled."
    )
    creator: PropertyRef = PropertyRef(
        "creator", extra_index=True, description="User name of the endpoint creator."
    )
    creation_timestamp: PropertyRef = PropertyRef(
        "creation_timestamp", description="Timestamp when the endpoint was created."
    )
    last_updated_timestamp: PropertyRef = PropertyRef(
        "last_updated_timestamp",
        description="Timestamp when the endpoint was last updated.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatabricksServingEndpointToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksWorkspace)-[:RESOURCE]->(:DatabricksServingEndpoint)
class DatabricksServingEndpointToWorkspaceRel(CartographyRelSchema):
    """A Databricks workspace contains this serving endpoint resource."""

    target_node_label: str = "DatabricksWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKSPACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DatabricksServingEndpointToWorkspaceRelProperties = (
        DatabricksServingEndpointToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class DatabricksServingEndpointSchema(CartographyNodeSchema):
    """A Databricks model serving endpoint."""

    label: str = "DatabricksServingEndpoint"
    properties: DatabricksServingEndpointNodeProperties = (
        DatabricksServingEndpointNodeProperties()
    )
    sub_resource_relationship: DatabricksServingEndpointToWorkspaceRel = (
        DatabricksServingEndpointToWorkspaceRel()
    )
    # ACL-target ontology label so the HAS_PERMISSION MatchLinks can target it.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([DATABRICKS_ACL_OBJECT])
