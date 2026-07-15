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

# The user resource in Microsoft Graph exposes hundreds of properties but, in
# practice, only a small subset is populated in most tenants.  We deliberately
# model *just* the commonly-used attributes to keep the graph lean.


@dataclass(frozen=True)
class EntraUserNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Entra user ID.")
    user_principal_name: PropertyRef = PropertyRef(
        "user_principal_name", description="User principal name."
    )
    display_name: PropertyRef = PropertyRef(
        "display_name", description="Display name of the user."
    )
    given_name: PropertyRef = PropertyRef(
        "given_name", description="Given name of the user."
    )
    surname: PropertyRef = PropertyRef("surname", description="Surname of the user.")
    # The SDK calls this `mail`; we surface it as `email` like the rest of Cartography
    email: PropertyRef = PropertyRef(
        "mail", extra_index=True, description="Primary email address of the user."
    )
    mobile_phone: PropertyRef = PropertyRef(
        "mobile_phone", description="Mobile phone number of the user."
    )
    business_phones: PropertyRef = PropertyRef(
        "business_phones", description="Business phone numbers of the user."
    )
    job_title: PropertyRef = PropertyRef(
        "job_title", description="Job title of the user."
    )
    department: PropertyRef = PropertyRef(
        "department", description="Department of the user."
    )
    company_name: PropertyRef = PropertyRef(
        "company_name", description="Company name associated with the user."
    )
    office_location: PropertyRef = PropertyRef(
        "office_location", description="Office location of the user."
    )
    employee_id: PropertyRef = PropertyRef(
        "employee_id", description="Employee identifier of the user."
    )
    employee_type: PropertyRef = PropertyRef(
        "employee_type", description="Employment type of the user."
    )
    city: PropertyRef = PropertyRef("city", description="City in the user's address.")
    state: PropertyRef = PropertyRef(
        "state", description="State or province in the user's address."
    )
    country: PropertyRef = PropertyRef(
        "country", description="Country or region in the user's address."
    )
    preferred_language: PropertyRef = PropertyRef(
        "preferred_language", description="Preferred language of the user."
    )
    account_enabled: PropertyRef = PropertyRef(
        "account_enabled", description="Whether the user account is enabled."
    )
    age_group: PropertyRef = PropertyRef(
        "age_group", description="Age group classification of the user."
    )
    manager_id: PropertyRef = PropertyRef(
        "manager_id", description="Entra user ID of the user's manager."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the latest Cartography update.",
    )


@dataclass(frozen=True)
class EntraTenantToUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:EntraUser)-[:REPORTS_TO]->(:EntraUser)
class EntraUserReportsToRel(CartographyRelSchema):
    """Links an Entra user to their manager."""

    target_node_label: str = "EntraUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("manager_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "REPORTS_TO"
    properties: EntraTenantToUserRelProperties = EntraTenantToUserRelProperties()


@dataclass(frozen=True)
# (:EntraUser)<-[:RESOURCE]-(:AzureTenant)
class EntraUserToTenantRel(CartographyRelSchema):
    """Links a Microsoft tenant to one of its Entra users."""

    target_node_label: str = "AzureTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TENANT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: EntraTenantToUserRelProperties = EntraTenantToUserRelProperties()


@dataclass(frozen=True)
class EntraUserSchema(CartographyNodeSchema):
    """A user account in Microsoft Entra ID."""

    label: str = "EntraUser"
    properties: EntraUserNodeProperties = EntraUserNodeProperties()
    sub_resource_relationship: EntraUserToTenantRel = EntraUserToTenantRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            EntraUserReportsToRel(),
        ]
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [
            "EntraIdentity",
            "UserAccount",
        ]  # UserAccount label is used for ontology mapping
    )
