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
    id: PropertyRef = PropertyRef("Id")
    name: PropertyRef = PropertyRef("Name", extra_index=True)
    developer_name: PropertyRef = PropertyRef("DeveloperName")
    parent_role_id: PropertyRef = PropertyRef("ParentRoleId")
    rollup_description: PropertyRef = PropertyRef("RollupDescription")
    portal_type: PropertyRef = PropertyRef("PortalType")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SalesforceUserRoleToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SalesforceUserRole)<-[:RESOURCE]-(:SalesforceOrganization)
class SalesforceUserRoleToOrganizationRel(CartographyRelSchema):
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
