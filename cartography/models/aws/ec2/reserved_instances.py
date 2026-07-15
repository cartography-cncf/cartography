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
class EC2ReservedInstanceNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "ReservedInstancesId", description="The ID of the Reserved Instance."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )
    region: PropertyRef = PropertyRef(
        "Region", set_in_kwargs=True, description="The region of the reserved instance."
    )
    availabilityzone: PropertyRef = PropertyRef(
        "AvailabilityZone",
        description="The Availability Zone in which the Reserved Instance can be used.",
    )
    duration: PropertyRef = PropertyRef(
        "Duration", description="The duration of the Reserved Instance, in seconds."
    )
    end: PropertyRef = PropertyRef(
        "End", description="The time when the Reserved Instance expires."
    )
    start: PropertyRef = PropertyRef(
        "Start", description="The date and time the Reserved Instance started."
    )
    count: PropertyRef = PropertyRef(
        "InstanceCount", description="The number of reservations purchased."
    )
    type: PropertyRef = PropertyRef(
        "InstanceType",
        description="The instance type on which the Reserved Instance can be used.",
    )
    productdescription: PropertyRef = PropertyRef(
        "ProductDescription",
        description="The Reserved Instance product platform description.",
    )
    state: PropertyRef = PropertyRef(
        "State", description="The state of the Reserved Instance purchase."
    )
    currencycode: PropertyRef = PropertyRef(
        "CurrencyCode",
        description="The currency of the Reserved Instance. It's specified using ISO 4217 standard currency codes.",
    )
    instancetenancy: PropertyRef = PropertyRef(
        "InstanceTenancy", description="The tenancy of the instance."
    )
    offeringclass: PropertyRef = PropertyRef(
        "OfferingClass", description="The offering class of the Reserved Instance."
    )
    offeringtype: PropertyRef = PropertyRef(
        "OfferingType", description="The Reserved Instance offering type."
    )
    scope: PropertyRef = PropertyRef(
        "Scope", description="The scope of the Reserved Instance."
    )
    fixedprice: PropertyRef = PropertyRef(
        "FixedPrice", description="The purchase price of the Reserved Instance."
    )


@dataclass(frozen=True)
class EC2ReservedInstanceToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EC2ReservedInstanceToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSEC2ReservedInstance`."

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: EC2ReservedInstanceToAWSAccountRelProperties = (
        EC2ReservedInstanceToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class EC2ReservedInstanceSchema(CartographyNodeSchema):
    "Represents an `AWSEC2ReservedInstance` node in the AWS graph."

    label: str = "AWSEC2ReservedInstance"
    # DEPRECATED: legacy EC2ReservedInstance node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["EC2ReservedInstance"])
    properties: EC2ReservedInstanceNodeProperties = EC2ReservedInstanceNodeProperties()
    sub_resource_relationship: EC2ReservedInstanceToAWSAccountRel = (
        EC2ReservedInstanceToAWSAccountRel()
    )
