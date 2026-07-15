from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class SalesforceProfileNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("Id", description="Salesforce profile ID.")
    name: PropertyRef = PropertyRef(
        "Name", extra_index=True, description="Profile name."
    )
    user_type: PropertyRef = PropertyRef(
        "UserType", description="User type to which the profile applies."
    )
    description: PropertyRef = PropertyRef(
        "Description", description="Profile description."
    )
    permissions_modify_all_data: PropertyRef = PropertyRef(
        "PermissionsModifyAllData",
        description="Whether the profile grants Modify All Data.",
    )
    permissions_view_all_data: PropertyRef = PropertyRef(
        "PermissionsViewAllData",
        description="Whether the profile grants View All Data.",
    )
    permissions_api_enabled: PropertyRef = PropertyRef(
        "PermissionsApiEnabled", description="Whether the profile grants API access."
    )
    permissions_manage_users: PropertyRef = PropertyRef(
        "PermissionsManageUsers",
        description="Whether the profile grants Manage Users.",
    )
    created_date: PropertyRef = PropertyRef(
        "CreatedDate", description="Profile creation timestamp."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last update.",
    )


@dataclass(frozen=True)
class SalesforceProfileToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SalesforceProfile)<-[:RESOURCE]-(:SalesforceOrganization)
class SalesforceProfileToOrganizationRel(CartographyRelSchema):
    """A Salesforce organization contains a profile."""

    target_node_label: str = "SalesforceOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SalesforceProfileToOrganizationRelProperties = (
        SalesforceProfileToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class SalesforceProfileSchema(CartographyNodeSchema):
    """A Salesforce baseline permission profile."""

    label: str = "SalesforceProfile"
    # PermissionRole label is used for ontology mapping
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["PermissionRole"])
    properties: SalesforceProfileNodeProperties = SalesforceProfileNodeProperties()
    sub_resource_relationship: SalesforceProfileToOrganizationRel = (
        SalesforceProfileToOrganizationRel()
    )
