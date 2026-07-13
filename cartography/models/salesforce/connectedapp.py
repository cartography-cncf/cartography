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
class SalesforceConnectedAppNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("Id")
    name: PropertyRef = PropertyRef("Name", extra_index=True)
    admin_approved_users_only: PropertyRef = PropertyRef(
        "OptionsAllowAdminApprovedUsersOnly"
    )
    created_date: PropertyRef = PropertyRef("CreatedDate")
    last_modified_date: PropertyRef = PropertyRef("LastModifiedDate")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SalesforceConnectedAppToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SalesforceConnectedApp)<-[:RESOURCE]-(:SalesforceOrganization)
class SalesforceConnectedAppToOrganizationRel(CartographyRelSchema):
    target_node_label: str = "SalesforceOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SalesforceConnectedAppToOrganizationRelProperties = (
        SalesforceConnectedAppToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class SalesforceConnectedAppToUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SalesforceConnectedApp)<-[:AUTHORIZED]-(:SalesforceUser)
# Authorizations are derived from the OAuthToken object (which user granted an
# OAuth token to which app).
class SalesforceConnectedAppToUserRel(CartographyRelSchema):
    target_node_label: str = "SalesforceUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("_authorized_user_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "AUTHORIZED"
    properties: SalesforceConnectedAppToUserRelProperties = (
        SalesforceConnectedAppToUserRelProperties()
    )


@dataclass(frozen=True)
class SalesforceConnectedAppSchema(CartographyNodeSchema):
    label: str = "SalesforceConnectedApp"
    # ThirdPartyApp label is used for ontology mapping
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["ThirdPartyApp"])
    properties: SalesforceConnectedAppNodeProperties = (
        SalesforceConnectedAppNodeProperties()
    )
    sub_resource_relationship: SalesforceConnectedAppToOrganizationRel = (
        SalesforceConnectedAppToOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            SalesforceConnectedAppToUserRel(),
        ]
    )
