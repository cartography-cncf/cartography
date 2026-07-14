from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels


@dataclass(frozen=True)
class SalesforceOrganizationNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("Id", description="Salesforce organization ID.")
    name: PropertyRef = PropertyRef("Name", description="Organization name.")
    organization_type: PropertyRef = PropertyRef(
        "OrganizationType", description="Salesforce organization edition."
    )
    instance_name: PropertyRef = PropertyRef(
        "InstanceName", description="Salesforce instance name."
    )
    is_sandbox: PropertyRef = PropertyRef(
        "IsSandbox", description="Whether the organization is a sandbox."
    )
    primary_contact: PropertyRef = PropertyRef(
        "PrimaryContact", description="Primary contact name."
    )
    country: PropertyRef = PropertyRef("Country", description="Organization country.")
    language_locale_key: PropertyRef = PropertyRef(
        "LanguageLocaleKey", description="Default language locale."
    )
    namespace_prefix: PropertyRef = PropertyRef(
        "NamespacePrefix", description="Managed package namespace prefix."
    )
    trial_expiration_date: PropertyRef = PropertyRef(
        "TrialExpirationDate", description="Trial expiration date."
    )
    created_date: PropertyRef = PropertyRef(
        "CreatedDate", description="Organization creation timestamp."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last update.",
    )


@dataclass(frozen=True)
class SalesforceOrganizationSchema(CartographyNodeSchema):
    """A Salesforce organization with the Tenant label."""

    label: str = "SalesforceOrganization"
    properties: SalesforceOrganizationNodeProperties = (
        SalesforceOrganizationNodeProperties()
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Tenant"])
