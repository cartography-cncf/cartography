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
    id: PropertyRef = PropertyRef("id")
    token_id: PropertyRef = PropertyRef("token_id", extra_index=True)
    comment: PropertyRef = PropertyRef("comment")
    creation_time: PropertyRef = PropertyRef("creation_time")
    expiry_time: PropertyRef = PropertyRef("expiry_time")
    owner_id: PropertyRef = PropertyRef("owner_id")
    created_by_id: PropertyRef = PropertyRef("created_by_id")
    created_by_username: PropertyRef = PropertyRef(
        "created_by_username", extra_index=True
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatabricksTokenToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksWorkspace)-[:RESOURCE]->(:DatabricksToken)
class DatabricksTokenToWorkspaceRel(CartographyRelSchema):
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
    label: str = "DatabricksToken"
    properties: DatabricksTokenNodeProperties = DatabricksTokenNodeProperties()
    sub_resource_relationship: DatabricksTokenToWorkspaceRel = (
        DatabricksTokenToWorkspaceRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [DatabricksTokenToOwnerUserRel(), DatabricksTokenToOwnerSPRel()],
    )
