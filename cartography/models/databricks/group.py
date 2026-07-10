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
class DatabricksGroupNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    scim_id: PropertyRef = PropertyRef("scim_id", extra_index=True)
    display_name: PropertyRef = PropertyRef("display_name", extra_index=True)
    external_id: PropertyRef = PropertyRef("external_id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatabricksGroupToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksWorkspace)-[:RESOURCE]->(:DatabricksGroup)
class DatabricksGroupToWorkspaceRel(CartographyRelSchema):
    target_node_label: str = "DatabricksWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKSPACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DatabricksGroupToWorkspaceRelProperties = (
        DatabricksGroupToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class DatabricksGroupToParentGroupRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksGroup)-[:MEMBER_OF]->(:DatabricksGroup)
class DatabricksGroupToParentGroupRel(CartographyRelSchema):
    target_node_label: str = "DatabricksGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("parent_group_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF"
    properties: DatabricksGroupToParentGroupRelProperties = (
        DatabricksGroupToParentGroupRelProperties()
    )


@dataclass(frozen=True)
class DatabricksGroupSchema(CartographyNodeSchema):
    label: str = "DatabricksGroup"
    properties: DatabricksGroupNodeProperties = DatabricksGroupNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["UserGroup"])
    sub_resource_relationship: DatabricksGroupToWorkspaceRel = (
        DatabricksGroupToWorkspaceRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [DatabricksGroupToParentGroupRel()],
    )
