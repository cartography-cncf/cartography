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
class SalesforcePermissionSetNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("Id", description="Salesforce permission set ID.")
    name: PropertyRef = PropertyRef(
        "Name", extra_index=True, description="Permission set API name."
    )
    label: PropertyRef = PropertyRef(
        "Label", description="Permission set display label."
    )
    description: PropertyRef = PropertyRef(
        "Description", description="Permission set description."
    )
    type: PropertyRef = PropertyRef("Type", description="Permission set type.")
    is_owned_by_profile: PropertyRef = PropertyRef(
        "IsOwnedByProfile",
        description="Whether the permission set is owned by a profile.",
    )
    profile_id: PropertyRef = PropertyRef(
        "ProfileId", description="Owning profile ID, when present."
    )
    permissions_modify_all_data: PropertyRef = PropertyRef(
        "PermissionsModifyAllData",
        description="Whether the permission set grants Modify All Data.",
    )
    permissions_view_all_data: PropertyRef = PropertyRef(
        "PermissionsViewAllData",
        description="Whether the permission set grants View All Data.",
    )
    permissions_api_enabled: PropertyRef = PropertyRef(
        "PermissionsApiEnabled",
        description="Whether the permission set grants API access.",
    )
    namespace_prefix: PropertyRef = PropertyRef(
        "NamespacePrefix", description="Managed package namespace prefix."
    )
    created_date: PropertyRef = PropertyRef(
        "CreatedDate", description="Permission set creation timestamp."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last update.",
    )


@dataclass(frozen=True)
class SalesforcePermissionSetToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SalesforcePermissionSet)<-[:RESOURCE]-(:SalesforceOrganization)
class SalesforcePermissionSetToOrganizationRel(CartographyRelSchema):
    """A Salesforce organization contains a permission set."""

    target_node_label: str = "SalesforceOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SalesforcePermissionSetToOrganizationRelProperties = (
        SalesforcePermissionSetToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class SalesforcePermissionSetToUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# Canonical ontology edge: (:UserAccount)-[:HAS_ROLE]->(:PermissionRole)
# (:SalesforcePermissionSet)<-[:HAS_ROLE]-(:SalesforceUser)
# Assignments come from the PermissionSetAssignment object.
class SalesforcePermissionSetToUserRel(CartographyRelSchema):
    """A Salesforce user has an assigned permission set role."""

    target_node_label: str = "SalesforceUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("_assignee_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_ROLE"
    properties: SalesforcePermissionSetToUserRelProperties = (
        SalesforcePermissionSetToUserRelProperties()
    )


@dataclass(frozen=True)
class SalesforcePermissionSetSchema(CartographyNodeSchema):
    """A Salesforce permission set with the PermissionRole label."""

    label: str = "SalesforcePermissionSet"
    # PermissionRole label is used for ontology mapping
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["PermissionRole"])
    properties: SalesforcePermissionSetNodeProperties = (
        SalesforcePermissionSetNodeProperties()
    )
    sub_resource_relationship: SalesforcePermissionSetToOrganizationRel = (
        SalesforcePermissionSetToOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            SalesforcePermissionSetToUserRel(),
        ]
    )
