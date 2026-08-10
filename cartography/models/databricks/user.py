from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.ontology.labels import USER_ACCOUNT


@dataclass(frozen=True)
class DatabricksUserNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Workspace-scoped identifier for the user."
    )
    scim_id: PropertyRef = PropertyRef(
        "scim_id", extra_index=True, description="Databricks SCIM user identifier."
    )
    user_name: PropertyRef = PropertyRef(
        "user_name", extra_index=True, description="SCIM user name of the user."
    )
    email: PropertyRef = PropertyRef(
        "email", extra_index=True, description="Primary email address of the user."
    )
    display_name: PropertyRef = PropertyRef(
        "display_name", description="Display name of the user."
    )
    external_id: PropertyRef = PropertyRef(
        "external_id",
        description="Identifier assigned by the external identity provider.",
    )
    active: PropertyRef = PropertyRef(
        "active", description="Whether the user account is active."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatabricksUserToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksWorkspace)-[:RESOURCE]->(:DatabricksUser)
class DatabricksUserToWorkspaceRel(CartographyRelSchema):
    """A Databricks workspace contains the user as a resource."""

    target_node_label: str = "DatabricksWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKSPACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DatabricksUserToWorkspaceRelProperties = (
        DatabricksUserToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class DatabricksUserToGroupRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksUser)-[:MEMBER_OF]->(:DatabricksGroup)
class DatabricksUserToGroupRel(CartographyRelSchema):
    """A Databricks principal is a member of a Databricks group."""

    target_node_label: str = "DatabricksGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("group_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF"
    properties: DatabricksUserToGroupRelProperties = (
        DatabricksUserToGroupRelProperties()
    )


@dataclass(frozen=True)
class DatabricksUserSchema(CartographyNodeSchema):
    """A user account in a Databricks workspace."""

    label: str = "DatabricksUser"
    properties: DatabricksUserNodeProperties = DatabricksUserNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([USER_ACCOUNT])
    sub_resource_relationship: DatabricksUserToWorkspaceRel = (
        DatabricksUserToWorkspaceRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [DatabricksUserToGroupRel()],
    )
