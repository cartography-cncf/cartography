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
class GSuiteUserNodeProperties(CartographyNodeProperties):
    """
    GSuite user node properties
    """

    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)

    # User identifiers and basic info
    user_id: PropertyRef = PropertyRef("id")  # Alias for id
    email: PropertyRef = PropertyRef("primaryEmail", extra_index=True)
    primary_email: PropertyRef = PropertyRef("primaryEmail")
    name: PropertyRef = PropertyRef("name")
    family_name: PropertyRef = PropertyRef("family_name")
    given_name: PropertyRef = PropertyRef("given_name")

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
class GSuiteUserToTenantRelProperties(CartographyRelProperties):
    """
    Properties for GSuite user to tenant relationship
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GSuiteUserToTenantRel(CartographyRelSchema):
    """
    Relationship from GSuite user to GSuite tenant
    """

    target_node_label: str = "GSuiteTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("CUSTOMER_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RESOURCE"
    properties: GSuiteUserToTenantRelProperties = GSuiteUserToTenantRelProperties()


@dataclass(frozen=True)
class GSuiteUserSchema(CartographyNodeSchema):
    """
    GSuite user node schema
    """

    label: str = "GSuiteUser"
    properties: GSuiteUserNodeProperties = GSuiteUserNodeProperties()
    sub_resource_relationship: GSuiteUserToTenantRel = GSuiteUserToTenantRel()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [
            "GCPPrincipal",
            "UserAccount",
        ]  # UserAccount label is used for ontology mapping
    )
