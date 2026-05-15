from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class AWSInternetGatewayNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("InternetGatewayId")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    ownerid: PropertyRef = PropertyRef("OwnerId")
    arn: PropertyRef = PropertyRef("Arn", extra_index=True)


@dataclass(frozen=True)
class AWSInternetGatewayToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSInternetGatewayToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AWSInternetGatewayToAWSAccountRelProperties = (
        AWSInternetGatewayToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class AWSInternetGatewayToAWSVpcRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSInternetGatewayToAWSVpcRel(CartographyRelSchema):
    target_node_label: str = "AWSVpc"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("VpcId")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ATTACHED_TO"
    properties: AWSInternetGatewayToAWSVpcRelProperties = (
        AWSInternetGatewayToAWSVpcRelProperties()
    )


@dataclass(frozen=True)
class AWSInternetGatewaySchema(CartographyNodeSchema):
    label: str = "AWSInternetGateway"
    properties: AWSInternetGatewayNodeProperties = AWSInternetGatewayNodeProperties()
    sub_resource_relationship: AWSInternetGatewayToAWSAccountRel = (
        AWSInternetGatewayToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AWSInternetGatewayToAWSVpcRel(),
        ],
    )
