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
class DatabricksProviderNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Metastore-scoped identifier for the Delta Sharing provider."
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Name of the provider."
    )
    metastore_id: PropertyRef = PropertyRef(
        "metastore_id",
        extra_index=True,
        description="Identifier of the containing Unity Catalog metastore.",
    )
    authentication_type: PropertyRef = PropertyRef(
        "authentication_type",
        description="Authentication method used by the provider.",
    )
    owner: PropertyRef = PropertyRef(
        "owner", extra_index=True, description="Owner of the provider."
    )
    comment: PropertyRef = PropertyRef(
        "comment", description="Comment associated with the provider."
    )
    data_provider_global_metastore_id: PropertyRef = PropertyRef(
        "data_provider_global_metastore_id",
        extra_index=True,
        description="Global metastore identifier of the data provider.",
    )
    cloud: PropertyRef = PropertyRef(
        "cloud", description="Cloud platform that hosts the provider."
    )
    region: PropertyRef = PropertyRef(
        "region", description="Cloud region that hosts the provider."
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Timestamp when the provider was created."
    )
    created_by: PropertyRef = PropertyRef(
        "created_by", description="Principal that created the provider."
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="Timestamp when the provider was last updated."
    )
    updated_by: PropertyRef = PropertyRef(
        "updated_by", description="Principal that last updated the provider."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatabricksProviderToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksWorkspace)-[:RESOURCE]->(:DatabricksProvider)
class DatabricksProviderToWorkspaceRel(CartographyRelSchema):
    """A Databricks workspace contains this provider resource."""

    target_node_label: str = "DatabricksWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKSPACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DatabricksProviderToWorkspaceRelProperties = (
        DatabricksProviderToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class DatabricksProviderToMetastoreRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksMetastore)-[:CONTAINS]->(:DatabricksProvider)
class DatabricksProviderToMetastoreRel(CartographyRelSchema):
    """A Unity Catalog metastore contains a Delta Sharing provider."""

    target_node_label: str = "DatabricksMetastore"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("metastore_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: DatabricksProviderToMetastoreRelProperties = (
        DatabricksProviderToMetastoreRelProperties()
    )


@dataclass(frozen=True)
class DatabricksProviderSchema(CartographyNodeSchema):
    """A Delta Sharing provider registered in Unity Catalog."""

    label: str = "DatabricksProvider"
    properties: DatabricksProviderNodeProperties = DatabricksProviderNodeProperties()
    sub_resource_relationship: DatabricksProviderToWorkspaceRel = (
        DatabricksProviderToWorkspaceRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [DatabricksProviderToMetastoreRel()],
    )
