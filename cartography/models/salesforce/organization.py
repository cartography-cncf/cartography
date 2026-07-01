from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels


@dataclass(frozen=True)
class SalesforceOrganizationNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("Id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("Name")
    instance_name: PropertyRef = PropertyRef("InstanceName")
    organization_type: PropertyRef = PropertyRef("OrganizationType")
    is_sandbox: PropertyRef = PropertyRef("IsSandbox")


@dataclass(frozen=True)
class SalesforceOrganizationSchema(CartographyNodeSchema):
    label: str = "SalesforceOrganization"
    properties: SalesforceOrganizationNodeProperties = (
        SalesforceOrganizationNodeProperties()
    )
    # The Salesforce org is the tenant, so it has no sub-resource relationship.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Tenant"])
