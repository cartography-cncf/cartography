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
class AWSCloudFrontDistributionNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("Id")
    arn: PropertyRef = PropertyRef("ARN", extra_index=True)
    domain_name: PropertyRef = PropertyRef("DomainName")
    status: PropertyRef = PropertyRef("Status")
    last_modified_time: PropertyRef = PropertyRef("LastModifiedTime")
    enabled: PropertyRef = PropertyRef("Enabled")
    comment: PropertyRef = PropertyRef("Comment")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSCloudFrontDistributionToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSCloudFrontDistributionToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AWSCloudFrontDistributionToAWSAccountRelProperties = (
        AWSCloudFrontDistributionToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class AWSCloudFrontDistributionSchema(CartographyNodeSchema):
    label: str = "AWSCloudFrontDistribution"
    properties: AWSCloudFrontDistributionNodeProperties = (
        AWSCloudFrontDistributionNodeProperties()
    )
    sub_resource_relationship: AWSCloudFrontDistributionToAWSAccountRel = (
        AWSCloudFrontDistributionToAWSAccountRel()
    )
