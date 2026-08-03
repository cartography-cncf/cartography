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
from cartography.models.ontology.labels import USER_ACCOUNT


@dataclass(frozen=True)
class DatabricksAccountUserNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Account-scoped Databricks SCIM user ID.",
    )
    scim_id: PropertyRef = PropertyRef(
        "scim_id",
        extra_index=True,
        description="Databricks account SCIM user ID.",
    )
    user_name: PropertyRef = PropertyRef(
        "user_name",
        extra_index=True,
        description="SCIM user name, typically the user's email address.",
    )
    email: PropertyRef = PropertyRef(
        "email",
        extra_index=True,
        description="Primary email address for the user.",
    )
    display_name: PropertyRef = PropertyRef(
        "display_name",
        description="User display name.",
    )
    external_id: PropertyRef = PropertyRef(
        "external_id",
        description="External identity provider ID for the user.",
    )
    active: PropertyRef = PropertyRef(
        "active",
        description="Whether the user is active.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatabricksAccountUserToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksAccount)-[:RESOURCE]->(:DatabricksAccountUser)
class DatabricksAccountUserToAccountRel(CartographyRelSchema):
    """A Databricks account owns an account-level resource."""

    target_node_label: str = "DatabricksAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DatabricksAccountUserToAccountRelProperties = (
        DatabricksAccountUserToAccountRelProperties()
    )


@dataclass(frozen=True)
class DatabricksAccountUserToGroupRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksAccountUser)-[:MEMBER_OF]->(:DatabricksAccountGroup)
class DatabricksAccountUserToGroupRel(CartographyRelSchema):
    """A Databricks account user is a member of an account group."""

    target_node_label: str = "DatabricksAccountGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("group_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF"
    properties: DatabricksAccountUserToGroupRelProperties = (
        DatabricksAccountUserToGroupRelProperties()
    )


@dataclass(frozen=True)
class DatabricksAccountUserSchema(CartographyNodeSchema):
    """A Databricks account-level SCIM user."""

    label: str = "DatabricksAccountUser"
    properties: DatabricksAccountUserNodeProperties = (
        DatabricksAccountUserNodeProperties()
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([USER_ACCOUNT])
    sub_resource_relationship: DatabricksAccountUserToAccountRel = (
        DatabricksAccountUserToAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [DatabricksAccountUserToGroupRel()],
    )
