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
class AWSRootPrincipalNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("arn")
    arn: PropertyRef = PropertyRef("arn", extra_index=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSRootPrincipalToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSRootPrincipalToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("AWS_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AWSRootPrincipalToAWSAccountRelProperties = (
        AWSRootPrincipalToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class AWSRootPrincipalSchema(CartographyNodeSchema):
    """
    Represents the AWS root principal for an AWS account
    """

    label: str = "AWSRootPrincipal"
    properties: AWSRootPrincipalNodeProperties = AWSRootPrincipalNodeProperties()
    sub_resource_relationship: AWSRootPrincipalToAWSAccountRel = (
        AWSRootPrincipalToAWSAccountRel()
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["AWSPrincipal"])
