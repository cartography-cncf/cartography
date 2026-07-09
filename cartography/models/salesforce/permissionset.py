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
    id: PropertyRef = PropertyRef("Id")
    name: PropertyRef = PropertyRef("Name", extra_index=True)
    label: PropertyRef = PropertyRef("Label")
    description: PropertyRef = PropertyRef("Description")
    type: PropertyRef = PropertyRef("Type")
    is_owned_by_profile: PropertyRef = PropertyRef("IsOwnedByProfile")
    profile_id: PropertyRef = PropertyRef("ProfileId")
    permissions_modify_all_data: PropertyRef = PropertyRef("PermissionsModifyAllData")
    permissions_view_all_data: PropertyRef = PropertyRef("PermissionsViewAllData")
    permissions_api_enabled: PropertyRef = PropertyRef("PermissionsApiEnabled")
    namespace_prefix: PropertyRef = PropertyRef("NamespacePrefix")
    created_date: PropertyRef = PropertyRef("CreatedDate")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SalesforcePermissionSetToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SalesforcePermissionSet)<-[:RESOURCE]-(:SalesforceOrganization)
class SalesforcePermissionSetToOrganizationRel(CartographyRelSchema):
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
