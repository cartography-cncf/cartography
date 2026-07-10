from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels


@dataclass(frozen=True)
class SalesforceOrganizationNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("Id")
    name: PropertyRef = PropertyRef("Name")
    organization_type: PropertyRef = PropertyRef("OrganizationType")
    instance_name: PropertyRef = PropertyRef("InstanceName")
    is_sandbox: PropertyRef = PropertyRef("IsSandbox")
    primary_contact: PropertyRef = PropertyRef("PrimaryContact")
    country: PropertyRef = PropertyRef("Country")
    language_locale_key: PropertyRef = PropertyRef("LanguageLocaleKey")
    namespace_prefix: PropertyRef = PropertyRef("NamespacePrefix")
    trial_expiration_date: PropertyRef = PropertyRef("TrialExpirationDate")
    created_date: PropertyRef = PropertyRef("CreatedDate")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SalesforceOrganizationSchema(CartographyNodeSchema):
    label: str = "SalesforceOrganization"
    properties: SalesforceOrganizationNodeProperties = (
        SalesforceOrganizationNodeProperties()
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Tenant"])
