from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels


@dataclass(frozen=True)
class AWSAccountNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="The AWS Account ID number")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )
    name: PropertyRef = PropertyRef("name", description="The name of the account")
    inscope: PropertyRef = PropertyRef(
        "inscope",
        set_in_kwargs=True,
        description="Indicates that the account is part of the sync scope (true or false).",
    )
    foreign: PropertyRef = PropertyRef(
        "foreign",
        description="Whether this account was discovered outside the configured AWS sync scope.",
    )


@dataclass(frozen=True)
class AWSAccountSchema(CartographyNodeSchema):
    "Represents an AWS account."

    label: str = "AWSAccount"
    properties: AWSAccountNodeProperties = AWSAccountNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Tenant"])
    scoped_cleanup: bool = False


@dataclass(frozen=True)
class AWSOrganizationAccountNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="The AWS Account ID number")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )
    name: PropertyRef = PropertyRef("name", description="The name of the account")
    arn: PropertyRef = PropertyRef(
        "arn",
        extra_index=True,
        description="The AWS Organizations ARN for this account, when discovered from AWS Organizations.",
    )
    email: PropertyRef = PropertyRef(
        "email",
        description="The email address associated with the account, when discovered from AWS Organizations.",
    )
    state: PropertyRef = PropertyRef(
        "state", description="The AWS Organizations account lifecycle state."
    )
    status: PropertyRef = PropertyRef(
        "status",
        description="The legacy AWS Organizations account status. AWS recommends using `state` instead.",
    )
    joined_method: PropertyRef = PropertyRef(
        "joined_method",
        description="The method by which the account joined the organization.",
    )
    joined_timestamp: PropertyRef = PropertyRef(
        "joined_timestamp", description="The date the account joined the organization."
    )
    org_id: PropertyRef = PropertyRef(
        "org_id",
        extra_index=True,
        description="The AWS Organization ID that contains this account, when available.",
    )


@dataclass(frozen=True)
class AWSOrganizationAccountSchema(CartographyNodeSchema):
    "Represents an AWS account."

    label: str = "AWSAccount"
    properties: AWSOrganizationAccountNodeProperties = (
        AWSOrganizationAccountNodeProperties()
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Tenant"])
    scoped_cleanup: bool = False
