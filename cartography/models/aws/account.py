from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels


@dataclass(frozen=True)
class AWSAccountNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")
    inscope: PropertyRef = PropertyRef("inscope", set_in_kwargs=True)
    foreign: PropertyRef = PropertyRef("foreign")


@dataclass(frozen=True)
class AWSAccountSchema(CartographyNodeSchema):
    label: str = "AWSAccount"
    properties: AWSAccountNodeProperties = AWSAccountNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Tenant"])
    scoped_cleanup: bool = False


@dataclass(frozen=True)
class AWSOrganizationAccountNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")
    arn: PropertyRef = PropertyRef("arn", extra_index=True)
    email: PropertyRef = PropertyRef("email")
    state: PropertyRef = PropertyRef("state")
    status: PropertyRef = PropertyRef("status")
    joined_method: PropertyRef = PropertyRef("joined_method")
    joined_timestamp: PropertyRef = PropertyRef("joined_timestamp")
    org_id: PropertyRef = PropertyRef("org_id", extra_index=True)


@dataclass(frozen=True)
class AWSOrganizationAccountSchema(CartographyNodeSchema):
    label: str = "AWSAccount"
    properties: AWSOrganizationAccountNodeProperties = (
        AWSOrganizationAccountNodeProperties()
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Tenant"])
    scoped_cleanup: bool = False
