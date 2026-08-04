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
class DatabricksTokenNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Workspace-scoped identifier for the token."
    )
    token_id: PropertyRef = PropertyRef(
        "token_id", extra_index=True, description="Databricks token identifier."
    )
    comment: PropertyRef = PropertyRef(
        "comment", description="Comment associated with the token."
    )
    creation_time: PropertyRef = PropertyRef(
        "creation_time", description="Timestamp when the token was created."
    )
    expiry_time: PropertyRef = PropertyRef(
        "expiry_time",
        description="Timestamp when the token expires, if it has an expiration.",
    )
    owner_id: PropertyRef = PropertyRef(
        "owner_id", description="Workspace-scoped identifier of the token owner."
    )
    created_by_id: PropertyRef = PropertyRef(
        "created_by_id",
        description="Workspace-scoped identifier of the principal that created the token.",
    )
    created_by_username: PropertyRef = PropertyRef(
        "created_by_username",
        extra_index=True,
        description="User name of the principal that created the token.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatabricksTokenToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksWorkspace)-[:RESOURCE]->(:DatabricksToken)
class DatabricksTokenToWorkspaceRel(CartographyRelSchema):
    """A Databricks workspace contains the token as a resource."""

    target_node_label: str = "DatabricksWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKSPACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DatabricksTokenToWorkspaceRelProperties = (
        DatabricksTokenToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class DatabricksTokenToOwnerUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksUser)-[:OWNER_OF]->(:DatabricksToken)
class DatabricksTokenToOwnerUserRel(CartographyRelSchema):
    """A Databricks principal owns the token."""

    target_node_label: str = "DatabricksUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("owner_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "OWNER_OF"
    properties: DatabricksTokenToOwnerUserRelProperties = (
        DatabricksTokenToOwnerUserRelProperties()
    )


@dataclass(frozen=True)
class DatabricksTokenToOwnerSPRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksServicePrincipal)-[:OWNER_OF]->(:DatabricksToken)
class DatabricksTokenToOwnerSPRel(CartographyRelSchema):
    """A Databricks principal owns the token."""

    target_node_label: str = "DatabricksServicePrincipal"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("owner_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "OWNER_OF"
    properties: DatabricksTokenToOwnerSPRelProperties = (
        DatabricksTokenToOwnerSPRelProperties()
    )


@dataclass(frozen=True)
class DatabricksTokenSchema(CartographyNodeSchema):
    """A Databricks personal access token and its ownership metadata."""

    label: str = "DatabricksToken"
    properties: DatabricksTokenNodeProperties = DatabricksTokenNodeProperties()
    sub_resource_relationship: DatabricksTokenToWorkspaceRel = (
        DatabricksTokenToWorkspaceRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [DatabricksTokenToOwnerUserRel(), DatabricksTokenToOwnerSPRel()],
    )
