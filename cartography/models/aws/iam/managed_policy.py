from dataclasses import dataclass

from cartography.models.aws.extra_labels import AWS_POLICY
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
    id: PropertyRef = PropertyRef(
        "id", description="Unique identifier for this `AWSManagedPolicy` node."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", description="Name of this `AWSManagedPolicy` node."
    )
    type: PropertyRef = PropertyRef(
        "type", description="Type of this `AWSManagedPolicy` node."
    )
    arn: PropertyRef = PropertyRef(
        "arn",
        extra_index=True,
        description="Amazon Resource Name (ARN) of this `AWSManagedPolicy` node.",
    )


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
    """Representation of an [AWS Policy](https://docs.aws.amazon.com/IAM/latest/APIReference/API_Policy.html) of type "managed". A managed policy is a built-in policy created and maintained by AWS. Managed policies are shared across principals, and as such are not associated with a specific AWSAccount."""

    label: str = "AWSManagedPolicy"
    properties: AWSManagedPolicyNodeProperties = AWSManagedPolicyNodeProperties()
    other_relationships: OtherRelationships = OtherRelationships(
        [AWSManagedPolicyToAWSPrincipalRel()]
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([AWS_POLICY])
