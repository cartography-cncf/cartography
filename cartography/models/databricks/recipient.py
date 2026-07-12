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
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name", extra_index=True)
    metastore_id: PropertyRef = PropertyRef("metastore_id", extra_index=True)
    # TOKEN = open sharing to any party holding a bearer token (external
    # exposure); DATABRICKS = sharing to another Databricks account.
    authentication_type: PropertyRef = PropertyRef("authentication_type")
    activated: PropertyRef = PropertyRef("activated")
    owner: PropertyRef = PropertyRef("owner", extra_index=True)
    comment: PropertyRef = PropertyRef("comment")
    data_recipient_global_metastore_id: PropertyRef = PropertyRef(
        "data_recipient_global_metastore_id", extra_index=True
    )
    cloud: PropertyRef = PropertyRef("cloud")
    region: PropertyRef = PropertyRef("region")
    created_at: PropertyRef = PropertyRef("created_at")
    created_by: PropertyRef = PropertyRef("created_by")
    updated_at: PropertyRef = PropertyRef("updated_at")
    updated_by: PropertyRef = PropertyRef("updated_by")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatabricksRecipientToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksWorkspace)-[:RESOURCE]->(:DatabricksRecipient)
class DatabricksRecipientToWorkspaceRel(CartographyRelSchema):
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
    label: str = "DatabricksRecipient"
    properties: DatabricksRecipientNodeProperties = DatabricksRecipientNodeProperties()
    sub_resource_relationship: DatabricksRecipientToWorkspaceRel = (
        DatabricksRecipientToWorkspaceRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [DatabricksRecipientToMetastoreRel()],
    )
