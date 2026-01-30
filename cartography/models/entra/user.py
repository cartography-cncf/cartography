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
    id: PropertyRef = PropertyRef("id")
    user_principal_name: PropertyRef = PropertyRef("user_principal_name")
    display_name: PropertyRef = PropertyRef("display_name")
    given_name: PropertyRef = PropertyRef("given_name")
    surname: PropertyRef = PropertyRef("surname")
    # The SDK calls this `mail`; we surface it as `email` like the rest of Cartography
    email: PropertyRef = PropertyRef("mail", extra_index=True)
    mobile_phone: PropertyRef = PropertyRef("mobile_phone")
    business_phones: PropertyRef = PropertyRef("business_phones")
    job_title: PropertyRef = PropertyRef("job_title")
    department: PropertyRef = PropertyRef("department")
    company_name: PropertyRef = PropertyRef("company_name")
    office_location: PropertyRef = PropertyRef("office_location")
    employee_id: PropertyRef = PropertyRef("employee_id")
    employee_type: PropertyRef = PropertyRef("employee_type")
    city: PropertyRef = PropertyRef("city")
    state: PropertyRef = PropertyRef("state")
    country: PropertyRef = PropertyRef("country")
    preferred_language: PropertyRef = PropertyRef("preferred_language")
    account_enabled: PropertyRef = PropertyRef("account_enabled")
    age_group: PropertyRef = PropertyRef("age_group")
    manager_id: PropertyRef = PropertyRef("manager_id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EntraTenantToUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:EntraUser)-[:REPORTS_TO]->(:EntraUser)
class EntraUserReportsToRel(CartographyRelSchema):
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
