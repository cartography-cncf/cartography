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
class GoogleWorkspaceUserNodeProperties(CartographyNodeProperties):
    """
    Google Workspace user node properties
    """

    id: PropertyRef = PropertyRef("id", description="Unique Google Workspace user ID.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last update.",
    )

    # User identifiers and basic info
    user_id: PropertyRef = PropertyRef(
        "id", description="Alias of the unique Google Workspace user ID."
    )
    primary_email: PropertyRef = PropertyRef(
        "primaryEmail",
        extra_index=True,
        description="Primary email address of the user.",
    )
    email: PropertyRef = PropertyRef(
        "primaryEmail",
        extra_index=True,
        description="Alias of the user's primary email address.",
    )
    name: PropertyRef = PropertyRef("name", description="Full name of the user.")
    family_name: PropertyRef = PropertyRef(
        "family_name", description="Family name of the user."
    )
    given_name: PropertyRef = PropertyRef(
        "given_name", description="Given name of the user."
    )

    # Organization info
    organization_name: PropertyRef = PropertyRef(
        "organization_name", description="Name of the user's primary organization."
    )
    organization_title: PropertyRef = PropertyRef(
        "organization_title", description="Title in the user's primary organization."
    )
    organization_department: PropertyRef = PropertyRef(
        "organization_department",
        description="Department in the user's primary organization.",
    )

    # Account settings
    agreed_to_terms: PropertyRef = PropertyRef(
        "agreedToTerms",
        description="Whether the user accepted the terms of service.",
    )
    archived: PropertyRef = PropertyRef(
        "archived", description="Whether the user account is archived."
    )
    change_password_at_next_login: PropertyRef = PropertyRef(
        "changePasswordAtNextLogin",
        description="Whether the user must change their password at next login.",
    )
    suspended: PropertyRef = PropertyRef(
        "suspended", description="Whether the user account is suspended."
    )

    # Admin and security settings
    is_admin: PropertyRef = PropertyRef(
        "isAdmin", description="Whether the user is a super administrator."
    )
    is_delegated_admin: PropertyRef = PropertyRef(
        "isDelegatedAdmin",
        description="Whether the user is a delegated administrator.",
    )
    is_enforced_in_2_sv: PropertyRef = PropertyRef(
        "isEnforcedIn2Sv",
        description="Whether two-step verification is enforced.",
    )
    is_enrolled_in_2_sv: PropertyRef = PropertyRef(
        "isEnrolledIn2Sv",
        description="Whether the user is enrolled in two-step verification.",
    )
    ip_whitelisted: PropertyRef = PropertyRef(
        "ipWhitelisted", description="Whether IP allowlisting applies to the user."
    )

    # Organization and profile
    org_unit_path: PropertyRef = PropertyRef(
        "orgUnitPath", description="Full path of the user's organizational unit."
    )
    include_in_global_address_list: PropertyRef = PropertyRef(
        "includeInGlobalAddressList",
        description="Whether the user appears in the global address list.",
    )
    is_mailbox_setup: PropertyRef = PropertyRef(
        "isMailboxSetup",
        description="Whether the user's Google mailbox is configured.",
    )

    # Timestamps and metadata
    creation_time: PropertyRef = PropertyRef(
        "creationTime", description="Time when the user account was created."
    )
    last_login_time: PropertyRef = PropertyRef(
        "lastLoginTime", description="Time of the user's last login."
    )
    etag: PropertyRef = PropertyRef("etag", description="API resource ETag.")
    kind: PropertyRef = PropertyRef("kind", description="API resource type.")

    # Photo information
    thumbnail_photo_etag: PropertyRef = PropertyRef(
        "thumbnailPhotoEtag", description="ETag of the user's thumbnail photo."
    )
    thumbnail_photo_url: PropertyRef = PropertyRef(
        "thumbnailPhotoUrl", description="URL of the user's thumbnail photo."
    )

    # Tenant relationship
    customer_id: PropertyRef = PropertyRef(
        "CUSTOMER_ID",
        set_in_kwargs=True,
        description="ID of the Google Workspace tenant that contains the user.",
    )


@dataclass(frozen=True)
class GoogleWorkspaceUserToTenantRelProperties(CartographyRelProperties):
    """
    Properties for Google Workspace user to tenant relationship
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GoogleWorkspaceUserToTenantRel(CartographyRelSchema):
    """A Google Workspace tenant contains a user account."""

    target_node_label: str = "GoogleWorkspaceTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("CUSTOMER_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GoogleWorkspaceUserToTenantRelProperties = (
        GoogleWorkspaceUserToTenantRelProperties()
    )


@dataclass(frozen=True)
class GoogleWorkspaceUserSchema(CartographyNodeSchema):
    """A Google Workspace user with canonical UserAccount and GCPPrincipal labels."""

    label: str = "GoogleWorkspaceUser"
    properties: GoogleWorkspaceUserNodeProperties = GoogleWorkspaceUserNodeProperties()
    sub_resource_relationship: GoogleWorkspaceUserToTenantRel = (
        GoogleWorkspaceUserToTenantRel()
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        ["UserAccount", "GCPPrincipal"]
    )
