from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class EntraUserNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    user_principal_name: PropertyRef = PropertyRef("user_principal_name")
    display_name: PropertyRef = PropertyRef("display_name")
    given_name: PropertyRef = PropertyRef("given_name")
    surname: PropertyRef = PropertyRef("surname")
    # The underlying datatype calls this 'mail' but everything else in cartography uses 'email'
    email: PropertyRef = PropertyRef("mail", extra_index=True)
    other_mails: PropertyRef = PropertyRef("other_mails")
    preferred_language: PropertyRef = PropertyRef("preferred_language")
    preferred_name: PropertyRef = PropertyRef("preferred_name")
    state: PropertyRef = PropertyRef("state")
    usage_location: PropertyRef = PropertyRef("usage_location")
    user_type: PropertyRef = PropertyRef("user_type")
    show_in_address_list: PropertyRef = PropertyRef("show_in_address_list")
    sign_in_sessions_valid_from_date_time: PropertyRef = PropertyRef(
        "sign_in_sessions_valid_from_date_time"
    )
    security_identifier: PropertyRef = PropertyRef("security_identifier")
    account_enabled: PropertyRef = PropertyRef("account_enabled")
    city: PropertyRef = PropertyRef("city")
    company_name: PropertyRef = PropertyRef("company_name")
    consent_provided_for_minor: PropertyRef = PropertyRef("consent_provided_for_minor")
    country: PropertyRef = PropertyRef("country")
    created_date_time: PropertyRef = PropertyRef("created_date_time")
    creation_type: PropertyRef = PropertyRef("creation_type")
    deleted_date_time: PropertyRef = PropertyRef("deleted_date_time")
    department: PropertyRef = PropertyRef("department")
    employee_id: PropertyRef = PropertyRef("employee_id")
    employee_type: PropertyRef = PropertyRef("employee_type")
    external_user_state: PropertyRef = PropertyRef("external_user_state")
    external_user_state_change_date_time: PropertyRef = PropertyRef(
        "external_user_state_change_date_time"
    )
    hire_date: PropertyRef = PropertyRef("hire_date")
    is_management_restricted: PropertyRef = PropertyRef("is_management_restricted")
    is_resource_account: PropertyRef = PropertyRef("is_resource_account")
    job_title: PropertyRef = PropertyRef("job_title")
    last_password_change_date_time: PropertyRef = PropertyRef(
        "last_password_change_date_time"
    )
    mail_nickname: PropertyRef = PropertyRef("mail_nickname")
    office_location: PropertyRef = PropertyRef("office_location")
    on_premises_distinguished_name: PropertyRef = PropertyRef(
        "on_premises_distinguished_name"
    )
    on_premises_domain_name: PropertyRef = PropertyRef("on_premises_domain_name")
    on_premises_immutable_id: PropertyRef = PropertyRef("on_premises_immutable_id")
    on_premises_last_sync_date_time: PropertyRef = PropertyRef(
        "on_premises_last_sync_date_time"
    )
    on_premises_sam_account_name: PropertyRef = PropertyRef(
        "on_premises_sam_account_name"
    )
    on_premises_security_identifier: PropertyRef = PropertyRef(
        "on_premises_security_identifier"
    )
    on_premises_sync_enabled: PropertyRef = PropertyRef("on_premises_sync_enabled")
    on_premises_user_principal_name: PropertyRef = PropertyRef(
        "on_premises_user_principal_name"
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EntraTenantToUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:EntraUser)<-[:RESOURCE]-(:AzureTenant)
class EntraUserToTenantRel(CartographyRelSchema):
    target_node_label: str = "AzureTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TENANT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: EntraTenantToUserRelProperties = EntraTenantToUserRelProperties()


@dataclass(frozen=True)
class EntraUserSchema(CartographyNodeSchema):
    label: str = "EntraUser"
    properties: EntraUserNodeProperties = EntraUserNodeProperties()
    sub_resource_relationship: EntraUserToTenantRel = EntraUserToTenantRel()
