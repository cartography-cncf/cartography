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
class SalesforceUserRoleNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("Id", description="Salesforce user role ID.")
    name: PropertyRef = PropertyRef(
        "Name", extra_index=True, description="User role name."
    )
    developer_name: PropertyRef = PropertyRef(
        "DeveloperName", description="User role API developer name."
    )
    parent_role_id: PropertyRef = PropertyRef(
        "ParentRoleId", description="ID of the parent role."
    )
    rollup_description: PropertyRef = PropertyRef(
        "RollupDescription", description="Role hierarchy rollup description."
    )
    portal_type: PropertyRef = PropertyRef(
        "PortalType", description="Portal type associated with the role."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last update.",
    )


@dataclass(frozen=True)
class SalesforceUserRoleToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SalesforceUserRole)<-[:RESOURCE]-(:SalesforceOrganization)
class SalesforceUserRoleToOrganizationRel(CartographyRelSchema):
    """A Salesforce organization contains a user role."""

    target_node_label: str = "SalesforceOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SalesforceUserRoleToOrganizationRelProperties = (
        SalesforceUserRoleToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class SalesforceUserRoleToParentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# Salesforce role hierarchy: a role reports up to its parent role.
# (:SalesforceUserRole)-[:MEMBER_OF]->(:SalesforceUserRole)
class SalesforceUserRoleToParentRel(CartographyRelSchema):
    """A Salesforce user role is a member of its parent role."""

    target_node_label: str = "SalesforceUserRole"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ParentRoleId")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF"
    properties: SalesforceUserRoleToParentRelProperties = (
        SalesforceUserRoleToParentRelProperties()
    )


@dataclass(frozen=True)
class SalesforceUserRoleSchema(CartographyNodeSchema):
    """A role in the Salesforce record-sharing hierarchy."""

    label: str = "SalesforceUserRole"
    properties: SalesforceUserRoleNodeProperties = SalesforceUserRoleNodeProperties()
    sub_resource_relationship: SalesforceUserRoleToOrganizationRel = (
        SalesforceUserRoleToOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            SalesforceUserRoleToParentRel(),
        ]
    )
