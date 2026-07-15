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


@dataclass(frozen=True)
class DatabricksConnectionNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    connection_id: PropertyRef = PropertyRef("connection_id", extra_index=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    full_name: PropertyRef = PropertyRef("full_name", extra_index=True)
    metastore_id: PropertyRef = PropertyRef("metastore_id", extra_index=True)
    connection_type: PropertyRef = PropertyRef("connection_type")
    credential_type: PropertyRef = PropertyRef("credential_type")
    owner: PropertyRef = PropertyRef("owner", extra_index=True)
    comment: PropertyRef = PropertyRef("comment")
    read_only: PropertyRef = PropertyRef("read_only")
    host: PropertyRef = PropertyRef("host", extra_index=True)
    port: PropertyRef = PropertyRef("port")
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")
    created_by: PropertyRef = PropertyRef("created_by")
    updated_by: PropertyRef = PropertyRef("updated_by")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatabricksConnectionToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksWorkspace)-[:RESOURCE]->(:DatabricksConnection)
class DatabricksConnectionToWorkspaceRel(CartographyRelSchema):
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
    label: str = "DatabricksConnection"
    properties: DatabricksConnectionNodeProperties = (
        DatabricksConnectionNodeProperties()
    )
    # Shared label so UC grants can target any grantable securable by one label.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["DatabricksSecurable"])
    sub_resource_relationship: DatabricksConnectionToWorkspaceRel = (
        DatabricksConnectionToWorkspaceRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [DatabricksConnectionToMetastoreRel()],
    )
