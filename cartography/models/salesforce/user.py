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
class SalesforceUserNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("Id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    username: PropertyRef = PropertyRef("Username", extra_index=True)
    name: PropertyRef = PropertyRef("Name")
    email: PropertyRef = PropertyRef("Email", extra_index=True)
    is_active: PropertyRef = PropertyRef("IsActive")
    user_type: PropertyRef = PropertyRef("UserType")
    profile_id: PropertyRef = PropertyRef("ProfileId")


@dataclass(frozen=True)
class SalesforceUserToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SalesforceOrganization)-[:RESOURCE]->(:SalesforceUser)
class SalesforceUserToOrganizationRel(CartographyRelSchema):
    target_node_label: str = "SalesforceOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SalesforceUserToOrganizationRelProperties = (
        SalesforceUserToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class SalesforceUserToProfileRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SalesforceUser)-[:HAS_PROFILE]->(:SalesforceProfile)
class SalesforceUserToProfileRel(CartographyRelSchema):
    target_node_label: str = "SalesforceProfile"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ProfileId")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_PROFILE"
    properties: SalesforceUserToProfileRelProperties = (
        SalesforceUserToProfileRelProperties()
    )


@dataclass(frozen=True)
class SalesforceUserToPermissionSetRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SalesforceUser)-[:HAS_PERMISSION_SET]->(:SalesforcePermissionSet)
class SalesforceUserToPermissionSetRel(CartographyRelSchema):
    target_node_label: str = "SalesforcePermissionSet"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("permission_set_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_PERMISSION_SET"
    properties: SalesforceUserToPermissionSetRelProperties = (
        SalesforceUserToPermissionSetRelProperties()
    )


@dataclass(frozen=True)
class SalesforceUserSchema(CartographyNodeSchema):
    label: str = "SalesforceUser"
    # UserAccount label is used for ontology mapping.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["UserAccount"])
    properties: SalesforceUserNodeProperties = SalesforceUserNodeProperties()
    sub_resource_relationship: SalesforceUserToOrganizationRel = (
        SalesforceUserToOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            SalesforceUserToProfileRel(),
            SalesforceUserToPermissionSetRel(),
        ]
    )
