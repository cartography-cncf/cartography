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
class DatabricksShareNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    share_id: PropertyRef = PropertyRef("share_id", extra_index=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    metastore_id: PropertyRef = PropertyRef("metastore_id", extra_index=True)
    owner: PropertyRef = PropertyRef("owner", extra_index=True)
    comment: PropertyRef = PropertyRef("comment")
    created_at: PropertyRef = PropertyRef("created_at")
    created_by: PropertyRef = PropertyRef("created_by")
    updated_at: PropertyRef = PropertyRef("updated_at")
    updated_by: PropertyRef = PropertyRef("updated_by")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatabricksShareToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksWorkspace)-[:RESOURCE]->(:DatabricksShare)
class DatabricksShareToWorkspaceRel(CartographyRelSchema):
    target_node_label: str = "DatabricksWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKSPACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DatabricksShareToWorkspaceRelProperties = (
        DatabricksShareToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class DatabricksShareToMetastoreRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksMetastore)-[:CONTAINS]->(:DatabricksShare)
class DatabricksShareToMetastoreRel(CartographyRelSchema):
    target_node_label: str = "DatabricksMetastore"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("metastore_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: DatabricksShareToMetastoreRelProperties = (
        DatabricksShareToMetastoreRelProperties()
    )


@dataclass(frozen=True)
class DatabricksShareToRecipientRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksShare)-[:SHARED_WITH]->(:DatabricksRecipient)
# Materialised from the share's permission assignments: which recipients have
# been granted access to the share.
class DatabricksShareToRecipientRel(CartographyRelSchema):
    target_node_label: str = "DatabricksRecipient"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("recipient_scoped_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "SHARED_WITH"
    properties: DatabricksShareToRecipientRelProperties = (
        DatabricksShareToRecipientRelProperties()
    )


@dataclass(frozen=True)
class DatabricksShareSchema(CartographyNodeSchema):
    label: str = "DatabricksShare"
    properties: DatabricksShareNodeProperties = DatabricksShareNodeProperties()
    sub_resource_relationship: DatabricksShareToWorkspaceRel = (
        DatabricksShareToWorkspaceRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            DatabricksShareToMetastoreRel(),
            DatabricksShareToRecipientRel(),
        ],
    )
