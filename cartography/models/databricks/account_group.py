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
from cartography.models.ontology.labels import USER_GROUP


@dataclass(frozen=True)
class DatabricksAccountGroupNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Account-scoped Databricks SCIM group ID.",
    )
    scim_id: PropertyRef = PropertyRef(
        "scim_id",
        extra_index=True,
        description="Databricks account SCIM group ID.",
    )
    display_name: PropertyRef = PropertyRef(
        "display_name",
        extra_index=True,
        description="Group display name.",
    )
    external_id: PropertyRef = PropertyRef(
        "external_id",
        description="External identity provider ID for the group.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatabricksAccountGroupToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksAccount)-[:RESOURCE]->(:DatabricksAccountGroup)
class DatabricksAccountGroupToAccountRel(CartographyRelSchema):
    """A Databricks account owns an account-level resource."""

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
    """A Databricks account group is a member of another account group."""

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
    """A Databricks account-level SCIM group."""

    label: str = "DatabricksAccountGroup"
    properties: DatabricksAccountGroupNodeProperties = (
        DatabricksAccountGroupNodeProperties()
    )
    # `UserGroup` matches the workspace-level DatabricksGroup and satisfies the
    # ontology MEMBER_OF constraints (UserAccount/ServiceAccount/UserGroup ->
    # UserGroup) for account principals nested into account groups.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([USER_GROUP])
    sub_resource_relationship: DatabricksAccountGroupToAccountRel = (
        DatabricksAccountGroupToAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [DatabricksAccountGroupToParentGroupRel()],
    )
