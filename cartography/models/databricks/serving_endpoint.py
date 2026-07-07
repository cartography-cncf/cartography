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


@dataclass(frozen=True)
class DatabricksServingEndpointNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name", extra_index=True)
    # System id the Permissions API keys off (distinct from the display name).
    endpoint_id: PropertyRef = PropertyRef("endpoint_id", extra_index=True)
    endpoint_type: PropertyRef = PropertyRef("endpoint_type")
    task: PropertyRef = PropertyRef("task")
    state_ready: PropertyRef = PropertyRef("state_ready")
    state_config_update: PropertyRef = PropertyRef("state_config_update")
    permission_level: PropertyRef = PropertyRef("permission_level")
    route_optimized: PropertyRef = PropertyRef("route_optimized")
    creator: PropertyRef = PropertyRef("creator", extra_index=True)
    creation_timestamp: PropertyRef = PropertyRef("creation_timestamp")
    last_updated_timestamp: PropertyRef = PropertyRef("last_updated_timestamp")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatabricksServingEndpointToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksWorkspace)-[:RESOURCE]->(:DatabricksServingEndpoint)
class DatabricksServingEndpointToWorkspaceRel(CartographyRelSchema):
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
    label: str = "DatabricksServingEndpoint"
    properties: DatabricksServingEndpointNodeProperties = (
        DatabricksServingEndpointNodeProperties()
    )
    sub_resource_relationship: DatabricksServingEndpointToWorkspaceRel = (
        DatabricksServingEndpointToWorkspaceRel()
    )
    # ACL-target ontology label so the HAS_PERMISSION MatchLinks can target it.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["DatabricksAclObject"])
