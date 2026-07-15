from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_source_node_matcher
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import SourceNodeMatcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class GoogleWorkspaceOAuthAppNodeProperties(CartographyNodeProperties):
    """
    Google Workspace OAuth app node properties
    Represents third-party applications that users have authorized
    https://developers.google.com/workspace/admin/directory/reference/rest/v1/tokens
    """

    id: PropertyRef = PropertyRef(
        "client_id", description="OAuth client ID used as the unique app ID."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last update.",
    )

    # App identifiers
    client_id: PropertyRef = PropertyRef(
        "client_id", extra_index=True, description="OAuth client ID of the app."
    )
    display_text: PropertyRef = PropertyRef(
        "display_text", description="Display name of the app."
    )

    # App properties
    anonymous: PropertyRef = PropertyRef(
        "anonymous", description="Whether access was granted anonymously."
    )
    native_app: PropertyRef = PropertyRef(
        "native_app", description="Whether the app is a native application."
    )

    # Tenant relationship
    customer_id: PropertyRef = PropertyRef(
        "CUSTOMER_ID",
        set_in_kwargs=True,
        description="ID of the Google Workspace tenant that contains the app.",
    )


@dataclass(frozen=True)
class GoogleWorkspaceUserToOAuthAppRelProperties(CartographyRelProperties):
    """
    Properties for Google Workspace user to OAuth app relationship (MatchLink)
    Includes the scopes granted by the user to the app
    """

    # Required fields for MatchLinks
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)

    # Custom property: scopes granted to the app
    scopes: PropertyRef = PropertyRef("scopes")


@dataclass(frozen=True)
class GoogleWorkspaceUserToOAuthAppRel(CartographyRelSchema):
    """A user authorized an OAuth app with the recorded scopes."""

    target_node_label: str = "GoogleWorkspaceOAuthApp"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "client_id": PropertyRef("client_id"),
        }
    )
    source_node_label: str = "GoogleWorkspaceUser"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {
            "id": PropertyRef("user_id"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "AUTHORIZED"
    properties: GoogleWorkspaceUserToOAuthAppRelProperties = (
        GoogleWorkspaceUserToOAuthAppRelProperties()
    )


@dataclass(frozen=True)
class GoogleWorkspaceOAuthAppToTenantRelProperties(CartographyRelProperties):
    """
    Properties for Google Workspace OAuth app to tenant relationship
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GoogleWorkspaceOAuthAppToTenantRel(CartographyRelSchema):
    """A Google Workspace tenant contains an authorized OAuth app."""

    target_node_label: str = "GoogleWorkspaceTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("CUSTOMER_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GoogleWorkspaceOAuthAppToTenantRelProperties = (
        GoogleWorkspaceOAuthAppToTenantRelProperties()
    )


@dataclass(frozen=True)
class GoogleWorkspaceOAuthAppSchema(CartographyNodeSchema):
    """An authorized OAuth app with the canonical ThirdPartyApp label."""

    label: str = "GoogleWorkspaceOAuthApp"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["ThirdPartyApp"])
    properties: GoogleWorkspaceOAuthAppNodeProperties = (
        GoogleWorkspaceOAuthAppNodeProperties()
    )
    sub_resource_relationship: GoogleWorkspaceOAuthAppToTenantRel = (
        GoogleWorkspaceOAuthAppToTenantRel()
    )
