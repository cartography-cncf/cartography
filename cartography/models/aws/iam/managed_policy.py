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
class AWSManagedPolicyNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")
    type: PropertyRef = PropertyRef("type")
    arn: PropertyRef = PropertyRef("arn", extra_index=True)


@dataclass(frozen=True)
class AWSManagedPolicyToAWSPrincipalRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSManagedPolicyToAWSPrincipalRel(CartographyRelSchema):
    target_node_label: str = "AWSPrincipal"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "arn": PropertyRef("principal_arns", one_to_many=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "POLICY"
    properties: AWSManagedPolicyToAWSPrincipalRelProperties = (
        AWSManagedPolicyToAWSPrincipalRelProperties()
    )


@dataclass(frozen=True)
class AWSManagedPolicySchema(CartographyNodeSchema):
    label: str = "AWSManagedPolicy"
    properties: AWSManagedPolicyNodeProperties = AWSManagedPolicyNodeProperties()
    other_relationships: OtherRelationships = OtherRelationships(
        [AWSManagedPolicyToAWSPrincipalRel()]
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["AWSPolicy"])
