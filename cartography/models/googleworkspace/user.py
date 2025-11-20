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

    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)

    # User identifiers and basic info
    user_id: PropertyRef = PropertyRef("id")  # Alias for id
    primary_email: PropertyRef = PropertyRef("primaryEmail", extra_index=True)
    email: PropertyRef = PropertyRef(
        "primaryEmail", extra_index=True
    )  # Alias for primary_email
    name: PropertyRef = PropertyRef("name")
    family_name: PropertyRef = PropertyRef("family_name")
    given_name: PropertyRef = PropertyRef("given_name")

    # Organization info
    organization_name: PropertyRef = PropertyRef("organization_name")
    organization_title: PropertyRef = PropertyRef("organization_title")
    organization_department: PropertyRef = PropertyRef("organization_department")

    # Account settings
    agreed_to_terms: PropertyRef = PropertyRef("agreedToTerms")
    archived: PropertyRef = PropertyRef("archived")
    change_password_at_next_login: PropertyRef = PropertyRef(
        "changePasswordAtNextLogin"
    )
    suspended: PropertyRef = PropertyRef("suspended")

    # Admin and security settings
    is_admin: PropertyRef = PropertyRef("isAdmin")
    is_delegated_admin: PropertyRef = PropertyRef("isDelegatedAdmin")
    is_enforced_in_2_sv: PropertyRef = PropertyRef("isEnforcedIn2Sv")
    is_enrolled_in_2_sv: PropertyRef = PropertyRef("isEnrolledIn2Sv")
    ip_whitelisted: PropertyRef = PropertyRef("ipWhitelisted")

    # Organization and profile
    org_unit_path: PropertyRef = PropertyRef("orgUnitPath")
    include_in_global_address_list: PropertyRef = PropertyRef(
        "includeInGlobalAddressList"
    )
    is_mailbox_setup: PropertyRef = PropertyRef("isMailboxSetup")

    # Timestamps and metadata
    creation_time: PropertyRef = PropertyRef("creationTime")
    last_login_time: PropertyRef = PropertyRef("lastLoginTime")
    etag: PropertyRef = PropertyRef("etag")
    kind: PropertyRef = PropertyRef("kind")

    # Photo information
    thumbnail_photo_etag: PropertyRef = PropertyRef("thumbnailPhotoEtag")
    thumbnail_photo_url: PropertyRef = PropertyRef("thumbnailPhotoUrl")

    # Tenant relationship
    customer_id: PropertyRef = PropertyRef("CUSTOMER_ID", set_in_kwargs=True)


@dataclass(frozen=True)
class GoogleWorkspaceUserToTenantRelProperties(CartographyRelProperties):
    """
    Properties for Google Workspace user to tenant relationship
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GoogleWorkspaceUserToTenantRel(CartographyRelSchema):
    """
    Relationship from Google Workspace user to Google Workspace tenant
    """

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
    """
    Google Workspace user node schema
    """

    label: str = "GoogleWorkspaceUser"
    properties: GoogleWorkspaceUserNodeProperties = GoogleWorkspaceUserNodeProperties()
    sub_resource_relationship: GoogleWorkspaceUserToTenantRel = (
        GoogleWorkspaceUserToTenantRel()
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["GCPPrincipal"])
