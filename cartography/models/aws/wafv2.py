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
class AWSWebACLNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("ARN")
    arn: PropertyRef = PropertyRef("ARN", extra_index=True)
    web_acl_id: PropertyRef = PropertyRef("Id")
    name: PropertyRef = PropertyRef("Name")
    description: PropertyRef = PropertyRef("Description")
    scope: PropertyRef = PropertyRef("Scope")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSWebACLToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AWSWebACL)<-[:RESOURCE]-(:AWSAccount)
class AWSWebACLToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AWSWebACLToAWSAccountRelProperties = (
        AWSWebACLToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class AWSWebACLToLoadBalancerV2RelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSWebACLToLoadBalancerV2Rel(CartographyRelSchema):
    """
    Created when a REGIONAL web ACL is associated with an application load balancer.
    (:AWSWebACL)-[:PROTECTS]->(:AWSLoadBalancerV2)
    """

    target_node_label: str = "AWSLoadBalancerV2"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("AlbArns", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "PROTECTS"
    properties: AWSWebACLToLoadBalancerV2RelProperties = (
        AWSWebACLToLoadBalancerV2RelProperties()
    )


@dataclass(frozen=True)
class AWSWebACLToAPIGatewayStageRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSWebACLToAPIGatewayStageRel(CartographyRelSchema):
    """
    Created when a REGIONAL web ACL is associated with an API Gateway REST API stage.
    Matches on the webaclarn property that the apigateway module already sets on stages.
    (:AWSWebACL)-[:PROTECTS]->(:APIGatewayStage)
    """

    target_node_label: str = "APIGatewayStage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"webaclarn": PropertyRef("ARN")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "PROTECTS"
    properties: AWSWebACLToAPIGatewayStageRelProperties = (
        AWSWebACLToAPIGatewayStageRelProperties()
    )


@dataclass(frozen=True)
class AWSWebACLToCloudFrontDistributionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSWebACLToCloudFrontDistributionRel(CartographyRelSchema):
    """
    Created when a CLOUDFRONT-scoped web ACL is associated with a distribution.
    Matches on the web_acl_id property that the cloudfront module sets on
    distributions, which holds the WAFv2 web ACL ARN.
    (:AWSWebACL)-[:PROTECTS]->(:CloudFrontDistribution)
    """

    target_node_label: str = "CloudFrontDistribution"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"web_acl_id": PropertyRef("ARN")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "PROTECTS"
    properties: AWSWebACLToCloudFrontDistributionRelProperties = (
        AWSWebACLToCloudFrontDistributionRelProperties()
    )


@dataclass(frozen=True)
class AWSWebACLSchema(CartographyNodeSchema):
    label: str = "AWSWebACL"
    properties: AWSWebACLNodeProperties = AWSWebACLNodeProperties()
    sub_resource_relationship: AWSWebACLToAWSAccountRel = AWSWebACLToAWSAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AWSWebACLToLoadBalancerV2Rel(),
            AWSWebACLToAPIGatewayStageRel(),
            AWSWebACLToCloudFrontDistributionRel(),
        ],
    )
