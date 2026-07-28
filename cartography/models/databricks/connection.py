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
from cartography.models.databricks.extra_labels import DATABRICKS_SECURABLE


@dataclass(frozen=True)
class DatabricksConnectionNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Metastore-scoped identifier for the connection."
    )
    connection_id: PropertyRef = PropertyRef(
        "connection_id",
        extra_index=True,
        description="Databricks identifier for the connection.",
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Name of the connection."
    )
    full_name: PropertyRef = PropertyRef(
        "full_name", extra_index=True, description="Full name of the connection."
    )
    metastore_id: PropertyRef = PropertyRef(
        "metastore_id",
        extra_index=True,
        description="Identifier of the metastore that contains the connection.",
    )
    connection_type: PropertyRef = PropertyRef(
        "connection_type", description="Type of the external data connection."
    )
    credential_type: PropertyRef = PropertyRef(
        "credential_type", description="Authentication method used by the connection."
    )
    owner: PropertyRef = PropertyRef(
        "owner", extra_index=True, description="Principal that owns the connection."
    )
    comment: PropertyRef = PropertyRef(
        "comment", description="User-provided description of the connection."
    )
    read_only: PropertyRef = PropertyRef(
        "read_only", description="Whether the connection permits only read operations."
    )
    host: PropertyRef = PropertyRef(
        "host", extra_index=True, description="Host name of the external data source."
    )
    port: PropertyRef = PropertyRef(
        "port", description="Network port of the external data source."
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Timestamp when the connection was created."
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="Timestamp when the connection was last updated."
    )
    created_by: PropertyRef = PropertyRef(
        "created_by", description="Principal that created the connection."
    )
    updated_by: PropertyRef = PropertyRef(
        "updated_by", description="Principal that last updated the connection."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatabricksConnectionToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksWorkspace)-[:RESOURCE]->(:DatabricksConnection)
class DatabricksConnectionToWorkspaceRel(CartographyRelSchema):
    """A Databricks connection is a resource within a workspace."""

    target_node_label: str = "DatabricksWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKSPACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DatabricksConnectionToWorkspaceRelProperties = (
        DatabricksConnectionToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class DatabricksConnectionToMetastoreRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksMetastore)-[:CONTAINS]->(:DatabricksConnection)
class DatabricksConnectionToMetastoreRel(CartographyRelSchema):
    """A Databricks metastore contains a connection."""

    target_node_label: str = "DatabricksMetastore"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("metastore_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: DatabricksConnectionToMetastoreRelProperties = (
        DatabricksConnectionToMetastoreRelProperties()
    )


@dataclass(frozen=True)
class DatabricksConnectionSchema(CartographyNodeSchema):
    """A Unity Catalog connection to an external data system."""

    label: str = "DatabricksConnection"
    properties: DatabricksConnectionNodeProperties = (
        DatabricksConnectionNodeProperties()
    )
    # Shared label so UC grants can target any grantable securable by one label.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([DATABRICKS_SECURABLE])
    sub_resource_relationship: DatabricksConnectionToWorkspaceRel = (
        DatabricksConnectionToWorkspaceRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [DatabricksConnectionToMetastoreRel()],
    )
