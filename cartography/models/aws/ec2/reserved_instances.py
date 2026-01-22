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
class EC2ReservedInstanceNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("ReservedInstancesId")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    availabilityzone: PropertyRef = PropertyRef("AvailabilityZone")
    duration: PropertyRef = PropertyRef("Duration")
    end: PropertyRef = PropertyRef("End")
    start: PropertyRef = PropertyRef("Start")
    count: PropertyRef = PropertyRef("InstanceCount")
    type: PropertyRef = PropertyRef("InstanceType")
    productdescription: PropertyRef = PropertyRef("ProductDescription")
    state: PropertyRef = PropertyRef("State")
    currencycode: PropertyRef = PropertyRef("CurrencyCode")
    instancetenancy: PropertyRef = PropertyRef("InstanceTenancy")
    offeringclass: PropertyRef = PropertyRef("OfferingClass")
    offeringtype: PropertyRef = PropertyRef("OfferingType")
    scope: PropertyRef = PropertyRef("Scope")
    fixedprice: PropertyRef = PropertyRef("FixedPrice")


@dataclass(frozen=True)
class EC2ReservedInstanceToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EC2ReservedInstanceToAWSAccountRel(CartographyRelSchema):
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
    label: str = "EC2ReservedInstance"
    properties: EC2ReservedInstanceNodeProperties = EC2ReservedInstanceNodeProperties()
    sub_resource_relationship: EC2ReservedInstanceToAWSAccountRel = (
        EC2ReservedInstanceToAWSAccountRel()
    )
