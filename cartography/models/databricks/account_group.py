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
class DatabricksAccountGroupNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    scim_id: PropertyRef = PropertyRef("scim_id", extra_index=True)
    display_name: PropertyRef = PropertyRef("display_name", extra_index=True)
    external_id: PropertyRef = PropertyRef("external_id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatabricksAccountGroupToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksAccount)-[:RESOURCE]->(:DatabricksAccountGroup)
class DatabricksAccountGroupToAccountRel(CartographyRelSchema):
    target_node_label: str = "DatabricksAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DatabricksAccountGroupToAccountRelProperties = (
        DatabricksAccountGroupToAccountRelProperties()
    )


@dataclass(frozen=True)
class DatabricksAccountGroupToParentGroupRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksAccountGroup)-[:MEMBER_OF]->(:DatabricksAccountGroup)
class DatabricksAccountGroupToParentGroupRel(CartographyRelSchema):
    target_node_label: str = "DatabricksAccountGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("parent_group_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF"
    properties: DatabricksAccountGroupToParentGroupRelProperties = (
        DatabricksAccountGroupToParentGroupRelProperties()
    )


@dataclass(frozen=True)
class DatabricksAccountGroupSchema(CartographyNodeSchema):
    label: str = "DatabricksAccountGroup"
    properties: DatabricksAccountGroupNodeProperties = (
        DatabricksAccountGroupNodeProperties()
    )
    # `UserGroup` matches the workspace-level DatabricksGroup and satisfies the
    # ontology MEMBER_OF constraints (UserAccount/ServiceAccount/UserGroup ->
    # UserGroup) for account principals nested into account groups.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["UserGroup"])
    sub_resource_relationship: DatabricksAccountGroupToAccountRel = (
        DatabricksAccountGroupToAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [DatabricksAccountGroupToParentGroupRel()],
    )
