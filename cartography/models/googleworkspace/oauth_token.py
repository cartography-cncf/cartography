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
class GoogleWorkspaceOAuthTokenNodeProperties(CartographyNodeProperties):
    """
    Google Workspace OAuth token node properties
    Represents third-party applications authorized by users
    https://developers.google.com/workspace/admin/directory/reference/rest/v1/tokens
    """

    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)

    # Token identifiers
    client_id: PropertyRef = PropertyRef("client_id", extra_index=True)
    display_text: PropertyRef = PropertyRef("display_text")

    # Token properties
    anonymous: PropertyRef = PropertyRef("anonymous")
    native_app: PropertyRef = PropertyRef("native_app")

    # Scopes granted to the application
    scopes: PropertyRef = PropertyRef("scopes")

    # User relationship
    user_key: PropertyRef = PropertyRef("user_key")

    # Tenant relationship
    customer_id: PropertyRef = PropertyRef("CUSTOMER_ID", set_in_kwargs=True)


@dataclass(frozen=True)
class GoogleWorkspaceOAuthTokenToUserRelProperties(CartographyRelProperties):
    """
    Properties for Google Workspace OAuth token to user relationship
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GoogleWorkspaceOAuthTokenToUserRel(CartographyRelSchema):
    """
    Relationship from Google Workspace OAuth token to Google Workspace user
    Indicates which user authorized this OAuth token
    """

    target_node_label: str = "GoogleWorkspaceUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("user_id"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "AUTHORIZED_BY"
    properties: GoogleWorkspaceOAuthTokenToUserRelProperties = (
        GoogleWorkspaceOAuthTokenToUserRelProperties()
    )


@dataclass(frozen=True)
class GoogleWorkspaceOAuthTokenToTenantRelProperties(CartographyRelProperties):
    """
    Properties for Google Workspace OAuth token to tenant relationship
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GoogleWorkspaceOAuthTokenToTenantRel(CartographyRelSchema):
    """
    Relationship from Google Workspace OAuth token to Google Workspace tenant
    """

    target_node_label: str = "GoogleWorkspaceTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("CUSTOMER_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GoogleWorkspaceOAuthTokenToTenantRelProperties = (
        GoogleWorkspaceOAuthTokenToTenantRelProperties()
    )


@dataclass(frozen=True)
class GoogleWorkspaceOAuthTokenSchema(CartographyNodeSchema):
    """
    Google Workspace OAuth token node schema
    """

    label: str = "GoogleWorkspaceOAuthToken"
    properties: GoogleWorkspaceOAuthTokenNodeProperties = (
        GoogleWorkspaceOAuthTokenNodeProperties()
    )
    sub_resource_relationship: GoogleWorkspaceOAuthTokenToTenantRel = (
        GoogleWorkspaceOAuthTokenToTenantRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [GoogleWorkspaceOAuthTokenToUserRel()],
    )
