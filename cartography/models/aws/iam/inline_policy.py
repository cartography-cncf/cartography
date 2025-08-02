from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class AWSInlinePolicyNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")
    type: PropertyRef = PropertyRef("type")
    arn: PropertyRef = PropertyRef("arn", extra_index=True)


@dataclass(frozen=True)
class AWSInlinePolicyToAWSPrincipalRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSInlinePolicyToAWSPrincipalRel(CartographyRelSchema):
    target_node_label: str = "AWSPrincipal"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "arn": PropertyRef("principal_arns", one_to_many=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "POLICY"
    properties: AWSInlinePolicyToAWSPrincipalRelProperties = (
        AWSInlinePolicyToAWSPrincipalRelProperties()
    )


@dataclass(frozen=True)
class AWSInlinePolicyToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSInlinePolicyToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("AWS_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AWSInlinePolicyToAWSAccountRelProperties = (
        AWSInlinePolicyToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class AWSInlinePolicySchema(CartographyNodeSchema):
    """
    Inline policies are defined on the given principal and are therefore scoped to that principal's account.
    """

    label: str = "AWSInlinePolicy"
    properties: AWSInlinePolicyNodeProperties = AWSInlinePolicyNodeProperties()
    sub_resource_relationship: AWSInlinePolicyToAWSAccountRel = (
        AWSInlinePolicyToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [AWSInlinePolicyToAWSPrincipalRel()]
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["AWSPolicy"])
