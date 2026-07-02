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
class DatabricksAppNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name", extra_index=True)
    description: PropertyRef = PropertyRef("description")
    url: PropertyRef = PropertyRef("url", extra_index=True)
    app_state: PropertyRef = PropertyRef("app_state")
    compute_state: PropertyRef = PropertyRef("compute_state")
    compute_size: PropertyRef = PropertyRef("compute_size")
    creator: PropertyRef = PropertyRef("creator", extra_index=True)
    # The app runs as this auto-provisioned service principal; its application
    # id is kept for the principal -> resource edge follow-up (PR8).
    service_principal_client_id: PropertyRef = PropertyRef(
        "service_principal_client_id", extra_index=True
    )
    service_principal_name: PropertyRef = PropertyRef("service_principal_name")
    oauth2_app_client_id: PropertyRef = PropertyRef("oauth2_app_client_id")
    create_time: PropertyRef = PropertyRef("create_time")
    update_time: PropertyRef = PropertyRef("update_time")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatabricksAppToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksWorkspace)-[:RESOURCE]->(:DatabricksApp)
class DatabricksAppToWorkspaceRel(CartographyRelSchema):
    target_node_label: str = "DatabricksWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKSPACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DatabricksAppToWorkspaceRelProperties = (
        DatabricksAppToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class DatabricksAppSchema(CartographyNodeSchema):
    label: str = "DatabricksApp"
    properties: DatabricksAppNodeProperties = DatabricksAppNodeProperties()
    sub_resource_relationship: DatabricksAppToWorkspaceRel = (
        DatabricksAppToWorkspaceRel()
    )
