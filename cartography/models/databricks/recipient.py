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
class DatabricksRecipientNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Metastore-scoped identifier for the Delta Sharing recipient."
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Name of the recipient."
    )
    metastore_id: PropertyRef = PropertyRef(
        "metastore_id",
        extra_index=True,
        description="Identifier of the containing Unity Catalog metastore.",
    )
    # TOKEN = open sharing to any party holding a bearer token (external
    # exposure); DATABRICKS = sharing to another Databricks account.
    authentication_type: PropertyRef = PropertyRef(
        "authentication_type",
        description="Authentication method used by the recipient.",
    )
    activated: PropertyRef = PropertyRef(
        "activated", description="Whether the recipient has been activated."
    )
    owner: PropertyRef = PropertyRef(
        "owner", extra_index=True, description="Owner of the recipient."
    )
    comment: PropertyRef = PropertyRef(
        "comment", description="Comment associated with the recipient."
    )
    data_recipient_global_metastore_id: PropertyRef = PropertyRef(
        "data_recipient_global_metastore_id",
        extra_index=True,
        description="Global metastore identifier of the data recipient.",
    )
    cloud: PropertyRef = PropertyRef(
        "cloud", description="Cloud platform that hosts the recipient."
    )
    region: PropertyRef = PropertyRef(
        "region", description="Cloud region that hosts the recipient."
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Timestamp when the recipient was created."
    )
    created_by: PropertyRef = PropertyRef(
        "created_by", description="Principal that created the recipient."
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="Timestamp when the recipient was last updated."
    )
    updated_by: PropertyRef = PropertyRef(
        "updated_by", description="Principal that last updated the recipient."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatabricksRecipientToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksWorkspace)-[:RESOURCE]->(:DatabricksRecipient)
class DatabricksRecipientToWorkspaceRel(CartographyRelSchema):
    """A Databricks workspace contains this recipient resource."""

    target_node_label: str = "DatabricksWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKSPACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DatabricksRecipientToWorkspaceRelProperties = (
        DatabricksRecipientToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class DatabricksRecipientToMetastoreRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksMetastore)-[:CONTAINS]->(:DatabricksRecipient)
class DatabricksRecipientToMetastoreRel(CartographyRelSchema):
    """A Unity Catalog metastore contains a Delta Sharing recipient."""

    target_node_label: str = "DatabricksMetastore"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("metastore_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: DatabricksRecipientToMetastoreRelProperties = (
        DatabricksRecipientToMetastoreRelProperties()
    )


@dataclass(frozen=True)
class DatabricksRecipientSchema(CartographyNodeSchema):
    """A Delta Sharing recipient registered in Unity Catalog."""

    label: str = "DatabricksRecipient"
    properties: DatabricksRecipientNodeProperties = DatabricksRecipientNodeProperties()
    sub_resource_relationship: DatabricksRecipientToWorkspaceRel = (
        DatabricksRecipientToWorkspaceRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [DatabricksRecipientToMetastoreRel()],
    )
