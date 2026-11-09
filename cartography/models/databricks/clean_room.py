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
class DatabricksCleanRoomNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Metastore-scoped identifier for the clean room."
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Name of the clean room."
    )
    metastore_id: PropertyRef = PropertyRef(
        "metastore_id",
        extra_index=True,
        description="Identifier of the metastore that contains the clean room.",
    )
    owner: PropertyRef = PropertyRef(
        "owner", extra_index=True, description="Principal that owns the clean room."
    )
    comment: PropertyRef = PropertyRef(
        "comment", description="User-provided description of the clean room."
    )
    access_restricted: PropertyRef = PropertyRef(
        "access_restricted",
        description="Whether access to the clean room is restricted.",
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Timestamp when the clean room was created."
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="Timestamp when the clean room was last updated."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatabricksCleanRoomToMetastoreResourceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksMetastore)-[:RESOURCE]->(:DatabricksCleanRoom)
class DatabricksCleanRoomToMetastoreResourceRel(CartographyRelSchema):
    """A Databricks clean room is a resource within a metastore."""

    target_node_label: str = "DatabricksMetastore"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("METASTORE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DatabricksCleanRoomToMetastoreResourceRelProperties = (
        DatabricksCleanRoomToMetastoreResourceRelProperties()
    )


@dataclass(frozen=True)
class DatabricksCleanRoomToMetastoreRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksMetastore)-[:CONTAINS]->(:DatabricksCleanRoom)
class DatabricksCleanRoomToMetastoreRel(CartographyRelSchema):
    """A Databricks metastore contains a clean room."""

    target_node_label: str = "DatabricksMetastore"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("metastore_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: DatabricksCleanRoomToMetastoreRelProperties = (
        DatabricksCleanRoomToMetastoreRelProperties()
    )


@dataclass(frozen=True)
class DatabricksCleanRoomSchema(CartographyNodeSchema):
    """A Databricks clean room for privacy-preserving data collaboration."""

    label: str = "DatabricksCleanRoom"
    properties: DatabricksCleanRoomNodeProperties = DatabricksCleanRoomNodeProperties()
    sub_resource_relationship: DatabricksCleanRoomToMetastoreResourceRel = (
        DatabricksCleanRoomToMetastoreResourceRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [DatabricksCleanRoomToMetastoreRel()],
    )
