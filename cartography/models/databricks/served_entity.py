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
class DatabricksServedEntityNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    served_name: PropertyRef = PropertyRef("served_name", extra_index=True)
    endpoint_name: PropertyRef = PropertyRef("endpoint_name", extra_index=True)
    entity_name: PropertyRef = PropertyRef("entity_name", extra_index=True)
    entity_type: PropertyRef = PropertyRef("entity_type")
    entity_version: PropertyRef = PropertyRef("entity_version")
    foundation_model_name: PropertyRef = PropertyRef("foundation_model_name")
    # For EXTERNAL_MODEL entities: the third-party provider data is routed to
    # (openai, anthropic, …) — a data-egress signal.
    external_model_provider: PropertyRef = PropertyRef("external_model_provider")
    external_model_name: PropertyRef = PropertyRef("external_model_name")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatabricksServedEntityToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksWorkspace)-[:RESOURCE]->(:DatabricksServedEntity)
class DatabricksServedEntityToWorkspaceRel(CartographyRelSchema):
    target_node_label: str = "DatabricksWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKSPACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DatabricksServedEntityToWorkspaceRelProperties = (
        DatabricksServedEntityToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class DatabricksServedEntityToEndpointRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksServingEndpoint)-[:SERVES]->(:DatabricksServedEntity)
class DatabricksServedEntityToEndpointRel(CartographyRelSchema):
    target_node_label: str = "DatabricksServingEndpoint"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("endpoint_scoped_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "SERVES"
    properties: DatabricksServedEntityToEndpointRelProperties = (
        DatabricksServedEntityToEndpointRelProperties()
    )


@dataclass(frozen=True)
class DatabricksServedEntitySchema(CartographyNodeSchema):
    label: str = "DatabricksServedEntity"
    properties: DatabricksServedEntityNodeProperties = (
        DatabricksServedEntityNodeProperties()
    )
    sub_resource_relationship: DatabricksServedEntityToWorkspaceRel = (
        DatabricksServedEntityToWorkspaceRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [DatabricksServedEntityToEndpointRel()],
    )
