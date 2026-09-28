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
class DatabricksAppNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Workspace-scoped identifier for the Databricks app."
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Name of the app."
    )
    description: PropertyRef = PropertyRef(
        "description", description="Description of the app."
    )
    url: PropertyRef = PropertyRef(
        "url", extra_index=True, description="URL of the deployed app."
    )
    app_state: PropertyRef = PropertyRef(
        "app_state", description="Current lifecycle state of the app."
    )
    compute_state: PropertyRef = PropertyRef(
        "compute_state", description="Current state of the app's compute."
    )
    compute_size: PropertyRef = PropertyRef(
        "compute_size", description="Compute size assigned to the app."
    )
    creator: PropertyRef = PropertyRef(
        "creator", extra_index=True, description="User name of the app creator."
    )
    # The app runs as this auto-provisioned service principal; its application
    # id is kept for the principal -> resource edge follow-up (PR8).
    service_principal_client_id: PropertyRef = PropertyRef(
        "service_principal_client_id",
        extra_index=True,
        description="Client identifier of the app's service principal.",
    )
    service_principal_name: PropertyRef = PropertyRef(
        "service_principal_name",
        description="Name of the app's service principal.",
    )
    oauth2_app_client_id: PropertyRef = PropertyRef(
        "oauth2_app_client_id",
        description="OAuth application client identifier for the app.",
    )
    create_time: PropertyRef = PropertyRef(
        "create_time", description="Timestamp when the app was created."
    )
    update_time: PropertyRef = PropertyRef(
        "update_time", description="Timestamp when the app was last updated."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatabricksAppToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksWorkspace)-[:RESOURCE]->(:DatabricksApp)
class DatabricksAppToWorkspaceRel(CartographyRelSchema):
    """A Databricks workspace contains this app resource."""

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
    """A Databricks app deployed in a workspace."""

    label: str = "DatabricksApp"
    properties: DatabricksAppNodeProperties = DatabricksAppNodeProperties()
    sub_resource_relationship: DatabricksAppToWorkspaceRel = (
        DatabricksAppToWorkspaceRel()
    )
    # ACL-target ontology label so the HAS_PERMISSION MatchLinks can target it.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([DATABRICKS_ACL_OBJECT])
