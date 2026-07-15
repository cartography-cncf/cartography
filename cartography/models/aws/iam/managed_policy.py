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
    id: PropertyRef = PropertyRef(
        "id", description="Unique identifier for this `AWSManagedPolicy` node."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that updated this `AWSManagedPolicy` node.",
    )
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
    "Represents a `POLICY` relationship from `AWSPrincipal` to `AWSManagedPolicy`."

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
    "Represents an `AWSManagedPolicy` node in the AWS graph."

    label: str = "AWSManagedPolicy"
    properties: AWSManagedPolicyNodeProperties = AWSManagedPolicyNodeProperties()
    other_relationships: OtherRelationships = OtherRelationships(
        [AWSManagedPolicyToAWSPrincipalRel()]
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["AWSPolicy"])
